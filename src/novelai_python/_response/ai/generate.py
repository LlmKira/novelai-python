from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from novelai_python.sdk.ai.generate._enum import TOKENIZER, TextLLMModel  # noqa
from novelai_python.tokenizer import LLMTokenizer
from novelai_python.utils.encode import b64_to_tokens

if TYPE_CHECKING:
    pass


class LLMResp(BaseModel):
    """
    response.json().get("output",None)
    """
    output: str
    text: str
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=False)

    @staticmethod
    def decode_token(token_str, model: TextLLMModel) -> str:
        return LLMTokenizer().decode(b64_to_tokens(token_str), tokenizer_name=TOKENIZER.get(model))
