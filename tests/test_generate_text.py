"""LLM request building (/ai/generate), offline: the tokenizer is a stand-in."""

import pytest

from novelai_python._enum import TextLLMModel, get_token_dtype
from novelai_python.sdk.ai import generate
from novelai_python.sdk.ai.generate import LLM


class FakeTokenizer:
    def encode(self, text):
        return [1, 70000] if text == "big" else [1, 2]  # 70000 needs the 32-bit wire format

    def total_tokens(self):
        return 128256


@pytest.fixture(autouse=True)
def fake_tokenizer(monkeypatch):
    monkeypatch.setattr(generate, "get_tokenizer", lambda name: FakeTokenizer())


def test_model_given_as_a_string_is_the_enum():
    from_enum = LLM.build("big", model=TextLLMModel.ERATO)
    from_json = LLM.model_validate({"input": "big", "model": "llama-3-erato-v1"})
    assert from_json.model is TextLLMModel.ERATO
    assert from_json.input == from_enum.input
    assert LLM.model_validate({"input": "hi", "model": "clio-v1"}).endpoint == "https://api.novelai.net"


def test_llama3_models_use_32_bit_tokens():
    assert get_token_dtype("llama-3-erato-v1") == "uint32"
    assert get_token_dtype(TextLLMModel.PURPLE) == "uint32"
    assert get_token_dtype(TextLLMModel.KAYRA) == "uint16"


def test_builds_do_not_share_the_preset():
    first = LLM.build("hi", model=TextLLMModel.ERATO)
    second = LLM.build("hi", model=TextLLMModel.ERATO)
    assert first.parameters.order and first.parameters.order == second.parameters.order
    assert first.parameters is not second.parameters
    assert first.advanced_setting is not second.advanced_setting
