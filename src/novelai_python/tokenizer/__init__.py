import functools
import gzip
import io
import json
import logging
import os
import pathlib
import re
import tempfile
import unicodedata
import zlib
from typing import Any, Literal

from curl_cffi import requests as curl_requests
from kitoken import Kitoken
from pydantic import BaseModel, model_validator

from ..credential._base import DEFAULT_USER_AGENT
from . import clip_tokenizer
from ._definition import added_token, bpe_model, js_regex

logger = logging.getLogger(__name__)

NormalizationForm = Literal["NFC", "NFD", "NFKC", "NFKD"]
_BYTE_TOKEN = re.compile(r"0x[0-9a-fA-F]{2}")
_CONTROL_TOKEN = re.compile(r"<\|.*\|>")  # <|endoftext|>, <|pad|>: dropped from decode() output


def download_file(url, destination_path, session) -> None:
    """
    Download a file from the specified URL and save it to the destination path.

    The file is written to a temporary sibling and renamed into place, so a crash or
    a concurrent process never leaves a half-written tokenizer behind.

    :param url: The URL to download the file from.
    :param destination_path: The path to save the downloaded file.
    :param session: a curl_cffi Session used for the download.
    :return: None
    :raises ValueError: If the downloaded file size doesn't match the Content-Length header.
    """
    response = session.get(
        url,
        timeout=30,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    response.raise_for_status()
    destination = pathlib.Path(destination_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as temp_file:
            temp_file.write(response.content)
        # mkstemp creates 0600; a cache dir shared between users must stay readable
        os.chmod(temp_name, 0o644)
        os.replace(temp_name, destination)
    except BaseException:
        pathlib.Path(temp_name).unlink(missing_ok=True)
        raise


class TokenizerSetting(BaseModel):
    pass


class ClipTokenizerSetting(TokenizerSetting):
    text: str


class LLMTokenizerSetting(TokenizerSetting):
    class TokenizerConfig(BaseModel):
        splitRegex: str
        maxEncodeChars: int | None = None
        maxNoWhitespaceChars: int | None = None
        ignoreMerges: bool | None = False
        # the site runs String.prototype.normalize on the text first; it takes these four forms only
        normalization: NormalizationForm | None = None

    config: TokenizerConfig
    specialTokens: list[str]
    vocab: dict[str, int]
    merges: list

    @model_validator(mode="after")
    def ensure(self):
        self.merges = [tuple(merge) for merge in self.merges]
        return self


def is_clip_model(model_name: str) -> bool:
    return model_name.lower().startswith("clip_tokenizer")


def is_t5_model(model_name: str) -> bool:
    return model_name.lower().startswith("t5_tokenizer")


def default_tokenizer_dir() -> pathlib.Path:
    """Where downloaded ``.def`` files are cached.

    The package directory is used when it is writable (editable installs); a system
    site-packages is often read-only, so fall back to the user cache. ``NOVELAI_TOKENIZER_DIR``
    overrides both.
    """
    override = os.environ.get("NOVELAI_TOKENIZER_DIR")
    if override:
        path = pathlib.Path(override)
    else:
        package_dir = pathlib.Path(__file__).parent
        if os.access(package_dir, os.W_OK):
            return package_dir
        cache_root = pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache"))
        path = cache_root / "novelai_python" / "tokenizer"
    path.mkdir(parents=True, exist_ok=True)
    return path


class NaiTokenizer:
    def __init__(
        self,
        model: str,
        tokenizer_model_path: pathlib.Path | None = None,
        download_session: curl_requests.Session | None = None,
    ) -> None:
        if not model.endswith(".def"):
            model = f"{model}.def"
        self.model_full_name = model
        self.tokenizer_setting: ClipTokenizerSetting | LLMTokenizerSetting | str | None = None
        if download_session is None:
            # Only an explicit proxy (NOVELAI_PROXY), never the environment's system proxy.
            px = os.environ.get("NOVELAI_PROXY")
            download_session = curl_requests.Session(
                impersonate="chrome", trust_env=False, proxies={"http": px, "https": px} if px else None
            )
        self._download_session = download_session
        if tokenizer_model_path is None:
            tokenizer_model_path = default_tokenizer_dir()
        self.tokenizer_model_path = tokenizer_model_path
        self._load_tokenizer_settings()
        # Ids the tokenizers post-processor wrapped every sequence with (T5: </s> at the end);
        # kitoken does not insert sequence templates itself.
        self._prefix_ids: list[int] = []
        self._suffix_ids: list[int] = []
        self._vocab: list[str] = []
        self._size = 0
        # BPE (the site's tokenizer): decode() keeps special tokens except control markers like <|endoftext|>
        self._control_ids: set[int] = set()
        self._decode_specials = False
        self._max_chars = 0
        self._normalization: NormalizationForm | None = None
        self.tokenizer: Kitoken = self._create_tokenizer()

    @staticmethod
    def get_model_download_url(model_full_name) -> str:
        return f"https://novelai.net/tokenizer/compressed/{model_full_name}?v=2&static=true"

    @staticmethod
    def _read_compressed_def(file_data: bytes) -> str:
        """
        Attempt to read and decompress compressed data, trying gzip first, followed by zlib and raw deflate.

        :param file_data: Compressed byte data.
        :return: Decompressed file content as a string.
        :raises RuntimeError: If decompression fails for all methods.
        """
        try:
            decompress_obj = zlib.decompressobj(-zlib.MAX_WBITS)
            return decompress_obj.decompress(file_data).decode("utf-8")
        except Exception as e:
            logger.debug(f"Error decompressing with raw deflate: {e}, trying gzip next.")

        try:
            with gzip.GzipFile(fileobj=io.BytesIO(file_data)) as gzip_file:
                return gzip_file.read().decode("utf-8")
        except Exception as e:
            logger.debug(f"Error decompressing with gzip: {e}, trying zlib next.")

        try:
            return zlib.decompress(file_data).decode("utf-8")
        except Exception as e:
            logger.debug(f"Error decompressing with zlib: {e}, trying raw deflate next.")

        raise RuntimeError("Failed to decompress the data using gzip, zlib, or raw deflate.")

    def _load_tokenizer_settings(self) -> None:
        """
        Load tokenizer settings from the model file.
        :return: None
        :raises FileNotFoundError: If the model file is not found.
        :raises ValueError: If the tokenizer settings are invalid.
        :raises LookupError: If the model file download fails.
        """
        model_path = self.tokenizer_model_path.joinpath(self.model_full_name)
        url = self.get_model_download_url(self.model_full_name)
        try:
            if not model_path.exists():
                download_file(url, model_path, self._download_session)
                logger.info(f"Tokenizer {self.model_full_name} downloaded.")
        except Exception as e:
            model_path.unlink(missing_ok=True)
            raise LookupError(f"Failed to download model {self.model_full_name} from {url}: {e}") from e
        try:
            decoded_str = self._read_compressed_def(model_path.read_bytes())
            data = json.loads(decoded_str)
        except (RuntimeError, ValueError):
            # A cached file can be truncated (it then decompresses to cut-off JSON) or stored
            # in the wrong encoding: fetch it again once instead of failing for good.
            logger.warning(f"Tokenizer {self.model_full_name} is corrupt, downloading it again.")
            model_path.unlink(missing_ok=True)
            try:
                download_file(url, model_path, self._download_session)
            except Exception as e:
                model_path.unlink(missing_ok=True)
                raise LookupError(f"Failed to download model {self.model_full_name} from {url}: {e}") from e
            decoded_str = self._read_compressed_def(model_path.read_bytes())
            data = json.loads(decoded_str)
        try:
            if is_clip_model(self.model_full_name):
                self.tokenizer_setting = ClipTokenizerSetting.model_validate(data)
            elif is_t5_model(self.model_full_name):
                self.tokenizer_setting = decoded_str
            else:
                self.tokenizer_setting = LLMTokenizerSetting.model_validate(data)
        except Exception as e:
            raise ValueError(
                f"Failed to load tokenizer settings: {e} for {model_path}",
                "report this issue to https://github.com/LlmKira/novelai-python/issues",
            ) from e

    def _create_tokenizer(self) -> Kitoken:
        setting = self.tokenizer_setting
        if isinstance(setting, ClipTokenizerSetting):
            definition, self._vocab = clip_tokenizer.clip_definition(setting.text)
            self._size = len(self._vocab)
        elif isinstance(setting, str):
            definition = self._t5_definition(setting)
        elif isinstance(setting, LLMTokenizerSetting):
            definition = self._bpe_definition(setting)
        else:
            raise ValueError(f"Invalid tokenizer setting: {setting}")
        return Kitoken.from_tokenizers(json.dumps(definition).encode("utf-8"))

    def _bpe_definition(self, setting: LLMTokenizerSetting) -> dict[str, Any]:
        """Built to give what the site's own BPE tokenizer gives (the class in the novelai.net bundle):

        - a vocabulary with byte tokens ``0x00``..``0xff`` (nerdstash) is character-level and encodes
          anything it has no token for, a newline or a digit, through those bytes; any other is
          byte-level, as GPT-2;
        - special tokens are the ones the vocabulary has; the site ignores the rest;
        - without ``ignoreMerges`` the site builds tokens from the merge list alone, so the tokens no
          merge produces (genji has 4277) are kept from kitoken, which works from the vocabulary.
        """
        vocab = setting.vocab
        for token, token_id in vocab.items():
            self._name_token(token_id, token)
        self._size = len(vocab)
        specials = [token for token in setting.specialTokens if token in vocab]
        self._control_ids = {vocab[token] for token in specials if _CONTROL_TOKEN.fullmatch(token)}
        self._decode_specials = True
        self._max_chars = setting.config.maxEncodeChars or 0
        self._normalization = setting.config.normalization
        byte_tokens = {token for token in vocab if _BYTE_TOKEN.fullmatch(token)}
        model_vocab = vocab
        if not setting.config.ignoreMerges:
            produced = {left + right for left, right in setting.merges}
            keep = produced | byte_tokens | set(specials)
            model_vocab = {token: i for token, i in vocab.items() if len(token) == 1 or token in keep}
        split = {
            "type": "Split",
            "pattern": {"Regex": js_regex(setting.config.splitRegex)},
            "behavior": "MergedWithNext",
            "invert": False,
        }
        if byte_tokens:
            # kitoken takes byte tokens as <0xNN>
            model_vocab = {(f"<{token}>" if token in byte_tokens else token): i for token, i in model_vocab.items()}
            pre_tokenizer, decoder = split, None
        else:
            byte_level = {"type": "ByteLevel", "add_prefix_space": False, "trim_offsets": True, "use_regex": False}
            pre_tokenizer = {"type": "Sequence", "pretokenizers": [split, byte_level]}
            decoder = {"type": "ByteLevel"}
        return {
            # longest first, as the site matches them: eight spaces are one special token, not four of two
            "added_tokens": [added_token(vocab[token], token) for token in sorted(specials, key=len, reverse=True)],
            "pre_tokenizer": pre_tokenizer,
            "decoder": decoder,
            "model": bpe_model(
                model_vocab,
                setting.merges,
                ignore_merges=bool(setting.config.ignoreMerges),
                byte_fallback=bool(byte_tokens),
            ),
        }

    def _t5_definition(self, raw: str) -> dict[str, Any]:
        """The file is a ``tokenizer.json`` already; only the template's special ids are taken out."""
        definition = json.loads(raw)
        post = definition.get("post_processor") or {}
        if post.get("type") == "TemplateProcessing":
            target = self._prefix_ids
            for piece in post["single"]:
                if "Sequence" in piece:
                    target = self._suffix_ids
                else:
                    target.extend(post["special_tokens"][piece["SpecialToken"]["id"]]["ids"])
        self._vocab = [token for token, _score in definition["model"]["vocab"]]
        for added in definition.get("added_tokens") or []:
            self._name_token(added["id"], added["content"])
        self._size = len(self._vocab)
        return definition

    def _name_token(self, token_id: int, token: str) -> None:
        if token_id >= len(self._vocab):
            self._vocab.extend([""] * (token_id + 1 - len(self._vocab)))
        self._vocab[token_id] = token

    @property
    def _is_clip(self) -> bool:
        return is_clip_model(self.model_full_name)

    def tokenize_text(self, text: str) -> list[str]:
        tokens = [self._vocab[i] for i in self.encode(text)]
        if self._is_clip:
            return [t.replace("</w>", " ") for t in tokens]
        return [token.replace("Ġ", " ") for token in tokens]

    def total_tokens(self) -> int:
        return self._size

    def encode(self, sentence: str) -> list[int]:
        if self._is_clip:
            return self.tokenizer.encode(clip_tokenizer.clean_text(sentence))
        if self._normalization:
            sentence = unicodedata.normalize(self._normalization, sentence)
        # Like the site, a text longer than maxEncodeChars is encoded in pieces of that many characters.
        step = self._max_chars or len(sentence) or 1
        ids = list(self._prefix_ids)
        for start in range(0, len(sentence), step):
            # True: special tokens in the text map to their ids, as with tokenizers' added tokens
            ids += self.tokenizer.encode(sentence[start : start + step], True)
        return ids + self._suffix_ids

    def decode(self, token_ids: list[int]) -> str:
        if self._is_clip:
            return clip_tokenizer.decode(self.tokenizer, token_ids)
        if self._control_ids:
            token_ids = [token_id for token_id in token_ids if token_id not in self._control_ids]
        return self.tokenizer.decode(token_ids, self._decode_specials).decode("utf-8", errors="replace")


@functools.cache
def get_tokenizer(model: str) -> NaiTokenizer:
    """The process-wide tokenizer for ``model``: building one parses a multi-megabyte file."""
    return NaiTokenizer(model)


# Example usage:
if __name__ == "__main__":
    tokenizer_package = NaiTokenizer("pile_tokenizer")
    t_text = "Hello, World! This is a   test."
    print(tokenizer_package.tokenize_text(t_text))
    print(tokenizer_package.encode(t_text))
    print(tokenizer_package.decode(tokenizer_package.encode(t_text)))
