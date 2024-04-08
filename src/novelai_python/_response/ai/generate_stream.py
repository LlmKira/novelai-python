from typing import Optional, Any, List

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
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=False)

    def text(self, model: TextLLMModel) -> str:
        return LLMTokenizer.decode(b64_to_tokens(self.token), tokenizer_name=TOKENIZER.get(model))

    @staticmethod
    def dispatch_stream(llm_response: List["LLMStreamResp"], model: TextLLMModel) -> List[str]:
        return [resp.text(model) for resp in llm_response]
