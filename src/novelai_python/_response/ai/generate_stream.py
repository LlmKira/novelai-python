from typing import Optional, Any

from pydantic import BaseModel, ConfigDict

from novelai_python.sdk.ai.generate._enum import TOKENIZER, TextLLMModel  # noqa
from novelai_python.tokenizer import LLMTokenizer
from novelai_python.utils.encode import b64_to_tokens


class LLMStreamResp(BaseModel):
    """
    {"token":"LRI=","ptr":0,"final":false,"logprobs":null}
    """
    token: str
    ptr: int
    final: bool
    logprobs: Optional[Any]
    text: Optional[str] = None
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=False)

    @staticmethod
    def decode(token_str, model: TextLLMModel) -> str:
        return LLMTokenizer().decode(b64_to_tokens(token_str), tokenizer_name=TOKENIZER.get(model))
