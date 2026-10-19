import io
import json
import zipfile
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import GenerateImageInfer, _retry


def _response(status: int, content: bytes, content_type: str):
    response = mock.Mock()
    response.status_code = status
    response.headers = {"Content-Type": content_type}
    response.content = content
    response.json = lambda: json.loads(content)
    return response


@pytest.mark.asyncio
async def test_retry_after_500_reuses_the_callers_open_session(monkeypatch):
    async def no_wait(_):
        return None

    monkeypatch.setattr(_retry.asyncio, "sleep", no_wait)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("image_0.webp", b"RIFF....WEBP")
    session = AsyncSession()
    post = mock.AsyncMock(
        side_effect=[
            _response(500, b'{"statusCode": 500, "message": "Error generating image"}', "application/json"),
            _response(200, buf.getvalue(), "binary/octet-stream"),
        ]
    )
    monkeypatch.setattr(session, "post", post)
    resp = await GenerateImageInfer.build_generate("1girl").request(session)
    assert post.await_count == 2
    assert resp.files == [("image_0.webp", b"RIFF....WEBP")]
    assert not session._closed  # the caller owns it
    await session.close()
