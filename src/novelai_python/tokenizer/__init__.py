# -*- coding: utf-8 -*-
import pathlib
from typing import List

import sentencepiece as spm


class TokenizerUtil:
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


if __name__ == "__main__":
    tokenizer_util = TokenizerUtil(TokenizerUtil.MODEL_V1_PATH)
    text = "The quick brown fox jumps over the goblin."
    token_id = tokenizer_util.encode(text)
    print("Token IDs:", token_id)
    decoded_text = tokenizer_util.decode(token_id)
    print("Decoded text:", decoded_text)
