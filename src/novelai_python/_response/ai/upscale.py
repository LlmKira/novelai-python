# @Time    : 2024/2/13 上午11:29
# @Author  : sudoskys
# @File    : upscale.py


from pydantic import BaseModel

from ..schema import RespBase


class UpscaleResp(RespBase):
    class RequestParams(BaseModel):
        endpoint: str
        raw_request: dict | None = None

    meta: RequestParams
    files: tuple[str, bytes] | None = None
