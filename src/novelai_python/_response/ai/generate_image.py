# @Time    : 2024/1/26 上午11:16
# @Author  : sudoskys
# @File    : generate_image.py

import pathlib
import time

from pydantic import BaseModel

from ..schema import RespBase


class RequestParams(BaseModel):
    endpoint: str
    raw_request: dict = None


class ImageStreamEvent(BaseModel):
    """
    One frame from /ai/generate-image-stream (msgpack framed with a uint32 big-endian length prefix).

    event_type: "intermediate" (preview), "final" (finished sample) or "error".
    """

    event_type: str
    samp_ix: int = 0
    step_ix: int | None = None
    image: bytes | None = None
    message: str | None = None

    @property
    def is_final(self) -> bool:
        return self.event_type == "final"

    @property
    def is_error(self) -> bool:
        return self.event_type == "error"


class ImageGenerateResp(RespBase):
    meta: RequestParams
    files: list[tuple[str, bytes]] = None

    def query_params(self, key: str, default=None):
        if not isinstance(self.meta.raw_request.get("parameters"), dict):
            raise Exception("Resp parameters is not dict")
        return self.meta.raw_request.get("parameters").get(key, default)

    def save(
        self,
        directory: str | pathlib.Path,
        *,
        prefix: str | None = None,
    ) -> list[pathlib.Path]:
        """
        Write every returned file into ``directory`` and return the paths.
        :param directory: created if missing
        :param prefix: filename prefix; defaults to seed + timestamp so repeated calls never collide
        """
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        if prefix is None:
            seed = self.query_params("seed", "noseed") if isinstance(self.meta.raw_request, dict) else "noseed"
            prefix = f"{seed}_{int(time.time() * 1000)}"
        written = []
        for index, (name, data) in enumerate(self.files or []):
            suffix = pathlib.Path(name).suffix or ".png"
            path = directory / f"{prefix}_{index}{suffix}"
            path.write_bytes(data)
            written.append(path)
        return written


class SuggestTagsResp(RespBase):
    class Tag(BaseModel):
        tag: str
        count: int
        confidence: float

    tags: list[Tag] = None
