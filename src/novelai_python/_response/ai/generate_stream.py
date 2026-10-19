from typing import Any

from pydantic import BaseModel, ConfigDict

from novelai_python._enum import TextLLMModelTypeAlias, get_token_dtype, get_tokenizer_model
from novelai_python.tokenizer import get_tokenizer
from novelai_python.utils.encode import b64_to_tokens


class LLMStreamResp(BaseModel):
    """
    {"token":"LRI=","ptr":0,"final":false,"logprobs":null}
    """

    token: str
    ptr: int
    final: bool
    logprobs: Any | None
    text: str | None = None
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=False)

    @staticmethod
    def decode(token_str, model: TextLLMModelTypeAlias) -> str:
        tokens = b64_to_tokens(token_str, dtype=get_token_dtype(model))
        return get_tokenizer(get_tokenizer_model(model)).decode(tokens)
