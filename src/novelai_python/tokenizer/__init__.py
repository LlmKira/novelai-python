# MIT:https://github.com/Aedial/novelai-api/blob/794c4f3d89cc86df3c7d2c401b320f1822822ac0/novelai_api/Tokenizer.py
# -*- coding: utf-8 -*-
import itertools
import pathlib
from pathlib import Path
from typing import Dict, List

import regex as re
import sentencepiece
import sentencepiece as spm
import tokenizers
from loguru import logger

from novelai_python.tokenizer.simple_tokenizer import SimpleTokenizer

tokenizers_path = Path(__file__).parent


# MIT:https://github.com/Aedial/novelai-api/blob/794c4f3d89cc86df3c7d2c401b320f1822822ac0/novelai_api/Tokenizer.py
class SentencePiece(sentencepiece.SentencePieceProcessor):
    """
    Wrapper around sentencepiece.SentencePieceProcessor that adds the encode and decode methods
    """

    trans_table_ids: Dict[int, str]
    trans_table_str: Dict[str, int]
    trans_regex_str: re.Pattern

    def __init__(self, model_path: str):
        super().__init__()
        self.Load(model_path)

        self.trans_table_ids = {
            self.unk_id(): "<|unk|>",
            self.pad_id(): "<|pad|>",
            self.bos_id(): "<|startoftext|>",
            self.eos_id(): "<|endoftext|>",
        }

        self.trans_table_str = {
            "<|unk|>": self.unk_id(),
            "<|pad|>": self.pad_id(),
            "<|startoftext|>": self.bos_id(),
            "<|endoftext|>": self.eos_id(),
        }

        trans_regex_keys = "|".join(re.escape(e) for e in self.trans_table_str)
        self.trans_regex_str = re.compile(trans_regex_keys)

    def encode(self, s: str) -> List[int]:
        """
        Encode the provided text using the SentencePiece tokenizer.
        This workaround is needed because sentencepiece cannot handle some tokens

        :param s: Text to encode

        :return: List of tokens the provided text encodes into
        """

        trans_table = self.trans_table_str

        # find the indexes of the string that need to be replaced
        indexes = list(self.trans_regex_str.finditer(s))

        # fast path, no translation needed
        if not indexes:
            return self.EncodeAsIds(s)

        # split the tokens into parts, using the indexes as separators and decode them
        parts = [
            s[0: indexes[0].start()],
            *[s[i.end() + 1: j.start()] for i, j in zip(indexes, indexes[1:])],
            s[indexes[-1].end() + 1:],
        ]
        encoded_parts: List[List[int]] = [self.EncodeAsIds(part) for part in parts]

        # translate the junctions
        junctions = [trans_table[i.group(0)] for i in indexes]

        # join the parts with the translated tokens
        return [
            *encoded_parts[0],
            *itertools.chain.from_iterable((j, *p) for j, p in zip(junctions, encoded_parts[1:])),
        ]

    def decode(self, t: List[int]):
        """
        Decode the provided tokens using the SentencePiece tokenizer.
        This workaround is needed because sentencepiece cannot handle some tokens

        :param t: Tokens to decode

        :return: Text the provided tokens decode into
        """

        trans_table = self.trans_table_ids

        # find the indexes of the string that need to be replaced
        indexes = [i for i, token in enumerate(t) if token in trans_table]

        # fast path, no translation needed
        if not indexes:
            return self.DecodeIds(t)

        # split the tokens into parts, using the indexes as separators and decode them
        parts = [
            t[0: indexes[0]],
            *[t[i + 1: j] for i, j in zip(indexes, indexes[1:])],
            t[indexes[-1] + 1:],
        ]
        decoded_parts = [self.DecodeIds(part) for part in parts]

        # translate the junctions
        junctions = [trans_table[t[i]] for i in indexes]

        # join the parts with the translated tokens
        return "".join((decoded_parts[0], *itertools.chain.from_iterable(zip(junctions, decoded_parts[1:]))))


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


# MIT: https://github.com/Aedial/novelai-api/blob/794c4f3d89cc86df3c7d2c401b320f1822822ac0/novelai_api/Tokenizer.py#L118
@singleton
class LLMTokenizer:
    """
    Abstraction of the tokenizer behind each Model
    """

    _GPT2_PATH = "gpt2_tokenizer.json"
    _GENJI_PATH = "gpt2-genji_tokenizer.json"
    _PILE_PATH = "pile_tokenizer.json"
    # ORIGIN TODO: check differences from NAI tokenizer (from my limited testing, there is None)
    _NERDSTASH_TOKENIZER_v1_PATH = "nerdstash_v1.model"
    _NERDSTASH_TOKENIZER_v2_PATH = "nerdstash_v2.model"

    def __init__(self, tokenizer_path=tokenizers_path):
        self._GPT2_TOKENIZER = tokenizers.Tokenizer.from_file(str(tokenizer_path / self._GPT2_PATH))
        self._GENJI_TOKENIZER = tokenizers.Tokenizer.from_file(str(tokenizer_path / self._GENJI_PATH))
        self._PILE_TOKENIZER = tokenizers.Tokenizer.from_file(str(tokenizer_path / self._PILE_PATH))
        self._CLIP_TOKENIZER = SimpleTokenizer()
        try:
            self._NERDSTASH_TOKENIZER_v1 = SentencePiece(str(tokenizer_path / self._NERDSTASH_TOKENIZER_v1_PATH))
            self._NERDSTASH_TOKENIZER_v2 = SentencePiece(str(tokenizer_path / self._NERDSTASH_TOKENIZER_v2_PATH))
        except FileNotFoundError as exc:
            logger.warning(
                "Nerdstash tokenizers not found, please check model path or "
                "there cannot be special text such as foreign languages, spaces, etc. in your model path."
            )
            raise exc
        self._tokenizers = {
            "gpt2": self._GPT2_TOKENIZER,
            "gpt2-genji": self._GENJI_TOKENIZER,
            "pile": self._PILE_TOKENIZER,
            "clip": self._CLIP_TOKENIZER,
            "nerdstash_v1": self._NERDSTASH_TOKENIZER_v1,
            "nerdstash_v2": self._NERDSTASH_TOKENIZER_v2,
        }

    def decode(self, o: List[int], tokenizer_name: str) -> str:
        if tokenizer_name not in self._tokenizers:
            raise NotImplementedError(f"Tokenizer {tokenizer_name} not recognized")
        tokenizer = self._tokenizers[tokenizer_name]

        return tokenizer.decode(o)

    def encode(self, o: str, tokenizer_name: str) -> List[int]:
        if tokenizer_name not in self._tokenizers:
            raise NotImplementedError(f"Tokenizer {tokenizer_name} not recognized")

        tokenizer = self._tokenizers[tokenizer_name]
        if isinstance(tokenizer, tokenizers.Tokenizer):
            return tokenizer.encode(o).ids
        if isinstance(tokenizer, (SimpleTokenizer, sentencepiece.SentencePieceProcessor)):
            return tokenizer.encode(o)
        raise ValueError(f"Tokenizer {tokenizer} ({tokenizer_name}) not recognized")


class ImagePromptTokenizer:
    MODEL_V1_PATH = pathlib.Path(__file__).parent.joinpath("novelai.model").absolute().as_posix()
    MODEL_V2_PATH = pathlib.Path(__file__).parent.joinpath("novelai_v2.model").absolute().as_posix()

    def __init__(self, model_path):
        self.tokenizer = spm.SentencePieceProcessor(model_file=model_path)  # noqa 401

    def encode(self, raw_text, readable: bool = False):
        if readable:
            return self.tokenizer.encode(raw_text, out_type=str)  # noqa 401
        return self.tokenizer.encode(raw_text)  # noqa 401

    def decode(self, token_ids: List[int]):
        return self.tokenizer.decode(token_ids)  # noqa 401


class TokenizerUtil(ImagePromptTokenizer):
    """
    Deprecated, use ImagePromptTokenizer instead
    """

    def __init__(self, model_path):
        super().__init__(model_path)

    def encode(self, raw_text, readable: bool = False):
        logger.warning("`TokenizerUtil` will deprecated, use `ImagePromptTokenizer` instead")
        return super().encode(raw_text, readable)

    def decode(self, token_ids: List[int]):
        logger.warning("`TokenizerUtil` will deprecated, use `ImagePromptTokenizer` instead")
        return super().decode(token_ids)


if __name__ == "__main__":
    tokenizer_util = ImagePromptTokenizer(ImagePromptTokenizer.MODEL_V1_PATH)
    text = "The quick brown fox jumps over the goblin."
    token_id = tokenizer_util.encode(text)
    print("Token IDs:", token_id)
    decoded_text = tokenizer_util.decode(token_id)
    print("Decoded text:", decoded_text)
