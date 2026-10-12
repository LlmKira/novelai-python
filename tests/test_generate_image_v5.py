# -*- coding: utf-8 -*-
import io
import json
import zipfile
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import GenerateImageInfer, DailyLimitExceeded
from novelai_python.credential._base import DEFAULT_USER_AGENT, browser_headers, CHROME_MAJOR_VERSION
from novelai_python.sdk.ai._enum import Model, get_uc_preset_id, is_v5_model
from novelai_python.sdk.ai.generate_image import build_multipart_request
from novelai_python.sdk.ai.generate_image.params import Params
from novelai_python.utils.daily_limit import DailyImageLimiter

# Shape captured from the novelai.net web client for nai-diffusion-5-full
WEB_CLIENT_V5_KEYS = {
    "params_version", "width", "height", "scale", "sampler", "steps", "n_samples",
    "ucPresetId", "qualityPresetId", "autoSmea", "dynamic_thresholding", "controlnet_strength",
    "legacy", "add_original_image", "cfg_rescale", "legacy_v3_extend", "use_coords", "legacy_uc",
    "normalize_reference_strength_multiple", "inpaintImg2ImgStrength", "seed", "characterPrompts",
    "straight_alpha", "tag_hint_qt", "tag_hint_uc_preset", "v4_prompt", "v4_negative_prompt",
    "negative_prompt", "deliberate_euler_ancestral_bug", "prefer_brownian", "noise_schedule", "image_format",
}
WEB_CLIENT_V5_HEAVY_UC = (
    "nsfw, lowres, artistic error, film grain, scan artifacts, worst quality, bad quality, jpeg artifacts, "
    "very displeasing, chromatic aberration, dithering, halftone, screentone, multiple views, logo, "
    "too many watermarks, negative space, blank page"
)


def test_v5_request_matches_web_client():
    gen = GenerateImageInfer.build_generate("1girl, cat girl", model=Model.NAI_DIFFUSION_5_FULL, use_trial=True)
    data = gen.model_dump(mode="json", exclude_none=True)
    params = data["parameters"]
    assert data["model"] == "nai-diffusion-5-full"
    assert data["input"] == "1girl, cat girl, very aesthetic, masterpiece, no text"
    assert set(params.keys()) == WEB_CLIENT_V5_KEYS
    assert params["params_version"] == 4
    assert params["scale"] == 7.0 and params["steps"] == 28
    assert params["ucPresetId"] == "heavy"
    assert params["qualityPresetId"] == "standard"
    assert params["image_format"] == "webp"
    assert params["straight_alpha"] is True
    assert params["tag_hint_qt"] == 1 and params["tag_hint_uc_preset"] == 2
    assert params["negative_prompt"] == WEB_CLIENT_V5_HEAVY_UC
    assert params["v4_negative_prompt"]["caption"]["base_caption"] == WEB_CLIENT_V5_HEAVY_UC
    assert "ucPreset" not in params and "qualityToggle" not in params
    assert "sm" not in params and "uncond_scale" not in params


def test_v5_uc_preset_ids():
    assert get_uc_preset_id(Model.NAI_DIFFUSION_5_FULL, 0) == "heavy"
    assert get_uc_preset_id(Model.NAI_DIFFUSION_5_FULL, 1) == "light"
    assert get_uc_preset_id(Model.NAI_DIFFUSION_5_FULL, 99) is None
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL, ucPreset=1)
    assert gen.parameters.ucPresetId == "light"
    assert is_v5_model("nai-diffusion-5-full") and not is_v5_model(Model.NAI_DIFFUSION_4_5_FULL)


def test_v5_model_forces_params_version_4():
    gen = GenerateImageInfer(
        input="1girl", model=Model.NAI_DIFFUSION_5_FULL, parameters=Params(params_version=3, ucPreset=0)
    )
    assert gen.parameters.params_version == 4
    assert gen.parameters.ucPresetId == "heavy"


def test_v45_request_keeps_legacy_shape():
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_4_5_FULL)
    params = gen.model_dump(mode="json", exclude_none=True)["parameters"]
    assert params["params_version"] == 3
    assert "ucPreset" in params and "qualityToggle" in params
    assert "ucPresetId" not in params and "image_format" not in params


def test_multipart_body_shape():
    body, content_type = build_multipart_request(b'{"a":1}')
    boundary = content_type.split("boundary=")[1]
    assert content_type.startswith("multipart/form-data; boundary=----WebKitFormBoundary")
    assert body.startswith(f"--{boundary}\r\n".encode())
    assert b'name="request"; filename="blob"' in body
    assert b"Content-Type: application/json\r\n\r\n" in body
    assert body.endswith(f"\r\n--{boundary}--\r\n".encode())


def test_browser_headers_use_latest_chrome():
    headers = browser_headers({"Authorization": "Bearer x"})
    assert headers["User-Agent"] == DEFAULT_USER_AGENT
    assert f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0" in DEFAULT_USER_AGENT
    assert f'"Google Chrome";v="{CHROME_MAJOR_VERSION}"' in headers["sec-ch-ua"]
    assert headers["Origin"] == "https://novelai.net"
    assert headers["Authorization"] == "Bearer x"


def _zip_response(files, content_type="binary/octet-stream"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files:
            zf.writestr(name, data)
    response = mock.Mock()
    response.headers = {"Content-Type": content_type}
    response.status_code = 200
    response.content = buf.getvalue()
    return response


def _session(response):
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=response)
    session.headers = {}
    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)
    return session


@pytest.mark.asyncio
async def test_v5_request_sends_multipart_and_counts_images(tmp_path):
    session = _session(_zip_response([("image_0.webp", b"RIFF....WEBP")]))
    limiter = DailyImageLimiter(5, state_file=tmp_path / "s.json")
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    resp = await gen.request(session, limiter=limiter)

    assert resp.files == [("image_0.webp", b"RIFF....WEBP")]
    assert limiter.used == 1
    call = session.post.await_args
    assert call.kwargs["headers"]["Content-Type"].startswith("multipart/form-data; boundary=")
    body = call.kwargs["data"]
    assert b'name="request"; filename="blob"' in body
    payload = json.loads(body.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n--", 1)[0])
    assert payload["model"] == "nai-diffusion-5-full"
    assert payload["parameters"]["ucPresetId"] == "heavy"


@pytest.mark.asyncio
async def test_v45_request_sends_json():
    session = _session(_zip_response([("image_0.png", b"\x89PNG")]))
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_4_5_FULL)
    await gen.request(session, limiter=False)
    call = session.post.await_args
    assert call.kwargs["headers"]["Content-Type"] == "application/json"
    assert json.loads(call.kwargs["data"])["model"] == "nai-diffusion-4-5-full"


@pytest.mark.asyncio
async def test_bare_webp_response_is_accepted():
    webp = b"RIFF\x00\x00\x00\x00WEBPVP8 "
    response = mock.Mock()
    response.headers = {"Content-Type": "image/webp"}
    response.status_code = 200
    response.content = webp
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    resp = await gen.request(_session(response), limiter=False)
    assert resp.files == [("image_0.webp", webp)]


@pytest.mark.asyncio
async def test_limit_blocks_before_sending(tmp_path):
    session = _session(_zip_response([("image_0.webp", b"x")]))
    limiter = DailyImageLimiter(1, state_file=tmp_path / "s.json")
    limiter.consume(1)
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    with pytest.raises(DailyLimitExceeded):
        await gen.request(session, limiter=limiter)
    session.post.assert_not_awaited()


def test_save_writes_files(tmp_path):
    from novelai_python._response.ai.generate_image import ImageGenerateResp, RequestParams
    resp = ImageGenerateResp(
        meta=RequestParams(endpoint="x", raw_request={"parameters": {"seed": 42}}),
        files=[("image_0.webp", b"a"), ("image_1.webp", b"b")],
    )
    paths = resp.save(tmp_path / "out", prefix="run")
    assert [p.name for p in paths] == ["run_0.webp", "run_1.webp"]
    assert (tmp_path / "out" / "run_1.webp").read_bytes() == b"b"
