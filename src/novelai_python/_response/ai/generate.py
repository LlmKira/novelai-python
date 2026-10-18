from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from novelai_python._enum import TextLLMModel, get_tokenizer_model
from novelai_python.tokenizer import NaiTokenizer
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
    def decode_token(token_str, model: TextLLMModel | str) -> str:
        dtype = "uint32" if model in [TextLLMModel.ERATO] else "uint16"
        return NaiTokenizer(model=get_tokenizer_model(model)).decode(b64_to_tokens(token_str, dtype=dtype))
