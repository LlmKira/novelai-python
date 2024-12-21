import gzip
import io
import json
import pathlib
import zlib
from typing import Dict, List, Optional

import httpx
from json_repair import repair_json
from loguru import logger
from pydantic import BaseModel, model_validator
from tokenizers import Tokenizer, pre_tokenizers, Regex, decoders
from tokenizers.models import BPE

from .clip_simple_tokenizer import SimpleTokenizer


def download_file(url, destination_path, session):
    """
    Download a file from the specified URL and save it to the destination path.

    :param url: The URL to download the file from.
    :param destination_path: The path to save the downloaded file.
    :param session: An httpx.Client instance to use for the download.
    :return: None
    :raises ValueError: If the downloaded file size doesn't match the Content-Length header.
    """
    response = session.get(url, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    with open(destination_path, "wb") as f:
        f.write(response.content)


class TokenizerSetting(BaseModel):
    pass


class ClipTokenizerSetting(TokenizerSetting):
    text: str


class LLMTokenizerSetting(TokenizerSetting):
    class TokenizerConfig(BaseModel):
        splitRegex: str
        maxEncodeChars: Optional[int] = None
        maxNoWhitespaceChars: Optional[int] = None
        ignoreMerges: Optional[bool] = False

    config: TokenizerConfig
    specialTokens: List[str]
    vocab: Dict[str, int]
    merges: list

    @model_validator(mode="after")
    def ensure(self):
        self.merges = [tuple(merge) for merge in self.merges]
        return self


def is_clip_model(model_name: str) -> bool:
    return model_name.lower().startswith("clip_tokenizer")


def is_t5_model(model_name: str) -> bool:
    return model_name.lower().startswith("t5_tokenizer")


class NaiTokenizer:
    def __init__(self,
                 model: str,
                 tokenizer_model_path: Optional[pathlib.Path] = None,
                 download_session: Optional[httpx.Client] = None,
                 ):
        if not model.endswith(".def"):
            model = f"{model}.def"
        self.model_full_name = model
        self.tokenizer_setting = None
        self.tokenizer = None
        if download_session is None:
            download_session = httpx.Client()
        self._download_session = download_session
        if tokenizer_model_path is None:
            tokenizer_model_path = pathlib.Path(__file__).parent
        self.tokenizer_model_path = tokenizer_model_path
        self._load_tokenizer_settings()
        self._create_tokenizer()

    @staticmethod
    def get_model_download_url(model_full_name):
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
            return decompress_obj.decompress(file_data).decode('utf-8')
        except Exception as e:
            logger.debug(f"Error decompressing with raw deflate: {e}, trying gzip next.")

        try:
            with gzip.GzipFile(fileobj=io.BytesIO(file_data)) as gzip_file:
                return gzip_file.read().decode('utf-8')
        except Exception as e:
            logger.debug(f"Error decompressing with gzip: {e}, trying zlib next.")

        try:
            return zlib.decompress(file_data).decode('utf-8')
        except Exception as e:
            logger.debug(f"Error decompressing with zlib: {e}, trying raw deflate next.")

        raise RuntimeError("Failed to decompress the data using gzip, zlib, or raw deflate.")

    def _load_tokenizer_settings(self):
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
            raise LookupError(f"Failed to download model {self.model_full_name} from {url}: {e}")
        model_bytes = model_path.read_bytes()
        decoded_str = self._read_compressed_def(model_bytes)
        repaired_data = repair_json(decoded_str, return_objects=True)
        try:
            if is_clip_model(self.model_full_name):
                self.tokenizer_setting = ClipTokenizerSetting.model_validate(repaired_data)
            elif is_t5_model(self.model_full_name):
                self.tokenizer_setting = json.dumps(repaired_data)
            else:
                self.tokenizer_setting = LLMTokenizerSetting.model_validate(repaired_data)
        except Exception as e:
            raise ValueError(
                f"Failed to load tokenizer settings: {e} for {model_path}",
                "report this issue to https://github.com/LlmKira/novelai-python/issues"
            )

    def _create_tokenizer(self):
        if is_clip_model(self.model_full_name):
            self._create_clip_tokenizer()
        elif is_t5_model(self.model_full_name):
            self.tokenizer = Tokenizer.from_str(self.tokenizer_setting)
        else:
            self._create_bpe_tokenizer()

    def _create_clip_tokenizer(self):
        setting = self.tokenizer_setting
        if not isinstance(setting, ClipTokenizerSetting):
            raise ValueError(f"Invalid tokenizer setting: {setting}")
        self.tokenizer = SimpleTokenizer(bpe_model_content=setting.text)

    def _create_bpe_tokenizer(self):
        setting = self.tokenizer_setting
        self.tokenizer = Tokenizer(BPE(
            vocab=setting.vocab,
            merges=setting.merges,
            ignore_merges=setting.config.ignoreMerges
        ))

        self.tokenizer.add_special_tokens(setting.specialTokens)
        if setting.config.maxEncodeChars:
            self.tokenizer.enable_truncation(max_length=setting.config.maxEncodeChars)

        pre_zus = [
            pre_tokenizers.Split(
                behavior="merged_with_next",
                pattern=Regex(setting.config.splitRegex)
            ),
        ]

        if self.tokenizer.token_to_id(" ") is None:
            pre_zus.append(pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False))

        pre_tokenizer = pre_tokenizers.Sequence(pre_zus)
        self.tokenizer.pre_tokenizer = pre_tokenizer  # noqa
        self.tokenizer.decoder = decoders.ByteLevel()  # noqa

    def tokenize_text(self, text: str) -> List[int]:
        if isinstance(self.tokenizer, Tokenizer):
            return [
                token.replace("Ġ", " ")  # .replace("Ċ", " ").replace("ċ", " ")
                for token in self.tokenizer.encode(text).tokens
            ]
        if isinstance(self.tokenizer, SimpleTokenizer):
            return self.tokenizer.encode(text).tokens
        raise NotImplementedError("Tokenizer does not support token encoding")

    def total_tokens(self) -> int:
        if isinstance(self.tokenizer, Tokenizer):
            return len(self.tokenizer.get_vocab())
        if isinstance(self.tokenizer, SimpleTokenizer):
            return len(self.tokenizer.get_vocab())
        raise NotImplementedError("Tokenizer does not support token encoding")

    def encode(self, sentence: str) -> List[int]:
        if isinstance(self.tokenizer, SimpleTokenizer):
            return self.tokenizer.encode(sentence).ids
        if isinstance(self.tokenizer, Tokenizer):
            return self.tokenizer.encode(sentence, add_special_tokens=True).ids
        raise NotImplementedError("Tokenizer does not support token encoding")

    def decode(self, token_ids: List[int]) -> str:
        if isinstance(self.tokenizer, SimpleTokenizer):
            return self.tokenizer.decode(token_ids)
        if isinstance(self.tokenizer, Tokenizer):
            return self.tokenizer.decode(token_ids)
        raise NotImplementedError("Tokenizer does not support token decoding")


# Example usage:
if __name__ == "__main__":
    tokenizer_package = NaiTokenizer("pile_tokenizer")
    t_text = "Hello, World! This is a   test."
    print(tokenizer_package.tokenize_text(t_text))
    print(tokenizer_package.encode(t_text))
    print(tokenizer_package.decode(tokenizer_package.encode(t_text)))
