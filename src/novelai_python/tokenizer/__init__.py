import functools
import gzip
import io
import json
import logging
import os
import pathlib
import tempfile
import zlib

from curl_cffi import requests as curl_requests
from pydantic import BaseModel, model_validator
from tokenizers import Regex, Tokenizer, decoders, pre_tokenizers
from tokenizers.models import BPE

from ..credential._base import DEFAULT_USER_AGENT
from . import clip_tokenizer

logger = logging.getLogger(__name__)


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
        self.tokenizer: Tokenizer = self._create_tokenizer()

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

    def _create_tokenizer(self) -> Tokenizer:
        setting = self.tokenizer_setting
        if isinstance(setting, ClipTokenizerSetting):
            return clip_tokenizer.build_clip_tokenizer(setting.text)
        if isinstance(setting, str):
            return Tokenizer.from_str(setting)
        if isinstance(setting, LLMTokenizerSetting):
            return self._create_bpe_tokenizer(setting)
        raise ValueError(f"Invalid tokenizer setting: {setting}")

    @staticmethod
    def _create_bpe_tokenizer(setting: LLMTokenizerSetting) -> Tokenizer:
        tokenizer = Tokenizer(
            BPE(vocab=setting.vocab, merges=setting.merges, ignore_merges=setting.config.ignoreMerges)
        )

        tokenizer.add_special_tokens(setting.specialTokens)
        if setting.config.maxEncodeChars:
            tokenizer.enable_truncation(max_length=setting.config.maxEncodeChars)

        pre_zus: list[pre_tokenizers.PreTokenizer] = [
            pre_tokenizers.Split(behavior="merged_with_next", pattern=Regex(setting.config.splitRegex)),
        ]

        if tokenizer.token_to_id(" ") is None:
            pre_zus.append(pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False))

        tokenizer.pre_tokenizer = pre_tokenizers.Sequence(pre_zus)
        tokenizer.decoder = decoders.ByteLevel()
        return tokenizer

    @property
    def _is_clip(self) -> bool:
        return is_clip_model(self.model_full_name)

    def tokenize_text(self, text: str) -> list[str]:
        if self._is_clip:
            return [t.replace("</w>", " ") for t in self.tokenizer.encode(clip_tokenizer.clean_text(text)).tokens]
        return [token.replace("Ġ", " ") for token in self.tokenizer.encode(text).tokens]

    def total_tokens(self) -> int:
        return self.tokenizer.get_vocab_size()

    def encode(self, sentence: str) -> list[int]:
        if self._is_clip:
            return self.tokenizer.encode(clip_tokenizer.clean_text(sentence)).ids
        return self.tokenizer.encode(sentence, add_special_tokens=True).ids

    def decode(self, token_ids: list[int]) -> str:
        if self._is_clip:
            return clip_tokenizer.decode(self.tokenizer, token_ids)
        return self.tokenizer.decode(token_ids)


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
