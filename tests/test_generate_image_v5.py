import io
import json
import zipfile
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import AuthError, DailyLimitExceeded, GenerateImageInfer
from novelai_python.credential._base import CHROME_MAJOR_VERSION, DEFAULT_USER_AGENT, browser_headers
from novelai_python.sdk.ai._enum import Model, get_uc_preset_id, is_v5_model
from novelai_python.sdk.ai.generate_image import build_multipart_request
from novelai_python.sdk.ai.generate_image.params import Params
from novelai_python.utils.daily_limit import DailyImageLimiter

# Shape captured from the novelai.net web client for nai-diffusion-5-full
WEB_CLIENT_V5_KEYS = {
    "params_version",
    "width",
    "height",
    "scale",
    "sampler",
    "steps",
    "n_samples",
    "ucPresetId",
    "qualityPresetId",
    "autoSmea",
    "dynamic_thresholding",
    "controlnet_strength",
    "legacy",
    "add_original_image",
    "cfg_rescale",
    "legacy_v3_extend",
    "use_coords",
    "legacy_uc",
    "normalize_reference_strength_multiple",
    "inpaintImg2ImgStrength",
    "seed",
    "characterPrompts",
    "straight_alpha",
    "tag_hint_qt",
    "tag_hint_uc_preset",
    "v4_prompt",
    "v4_negative_prompt",
    "negative_prompt",
    "deliberate_euler_ancestral_bug",
    "prefer_brownian",
    "noise_schedule",
    "image_format",
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
    assert params["scale"] == 7.0 and params["steps"] == 23
    assert params["ucPresetId"] == "heavy"
    assert params["qualityPresetId"] == "standard"
    assert params["image_format"] == "png"
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


def test_v45_request_uses_params_version_4_too():
    # the web client migrated every model to ucPresetId / qualityPresetId
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_4_5_FULL)
    params = gen.model_dump(mode="json", exclude_none=True)["parameters"]
    assert params["params_version"] == 4
    assert params["ucPresetId"] == "heavy" and params["qualityPresetId"] == "standard"
    assert "ucPreset" not in params and "qualityToggle" not in params
    # as the web client: V4.5 also sends image_format=webp,
    # but straight_alpha stays V5-only
    assert params["image_format"] == "png" and "straight_alpha" not in params


def test_v5_family_models():
    from novelai_python.sdk.ai._enum import INPAINTING_MODEL_LIST, V5_MODEL_LIST, get_supported_params

    assert Model.NAI_DIFFUSION_5_CURATED in V5_MODEL_LIST
    assert Model.NAI_DIFFUSION_5_FULL_INPAINTING in INPAINTING_MODEL_LIST
    assert get_supported_params(Model.NAI_DIFFUSION_5_CURATED).img2imgInpainting is True
    medium = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL_MEDIUM, steps=40, ucPreset=1)
    assert medium.parameters.steps == 14 and medium.parameters.ucPresetId == "heavy"


def test_quality_presets():
    from novelai_python.sdk.ai._enum import QualityPreset, get_quality_presets

    ids = [q.id for q in get_quality_presets(Model.NAI_DIFFUSION_5_FULL)]
    assert ids == ["standard", "light", "none"]
    light = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    light.parameters.qualityPresetId = QualityPreset.LIGHT
    light = GenerateImageInfer(input="1girl", model=Model.NAI_DIFFUSION_5_FULL, parameters=light.parameters)
    assert light.input.endswith(", very aesthetic, amazing quality, no text")
    off = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL, qualityToggle=False)
    assert off.input == "1girl" and off.parameters.qualityPresetId == QualityPreset.NONE


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
    assert headers["user-agent"] == DEFAULT_USER_AGENT
    assert f"Chrome/{CHROME_MAJOR_VERSION}.0.0.0" in DEFAULT_USER_AGENT
    assert f'"Google Chrome";v="{CHROME_MAJOR_VERSION}"' in headers["sec-ch-ua"]
    assert headers["origin"] == "https://novelai.net"
    assert headers["authorization"] == "Bearer x"


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
async def test_legacy_params_version_3_sends_json():
    session = _session(_zip_response([("image_0.png", b"\x89PNG")]))
    gen = GenerateImageInfer(
        input="1girl", model=Model.NAI_DIFFUSION_3, parameters=Params(params_version=3, ucPreset=0)
    )
    await gen.request(session, limiter=False)
    call = session.post.await_args
    assert call.kwargs["headers"]["Content-Type"] == "application/json"
    assert json.loads(call.kwargs["data"])["parameters"]["ucPreset"] == 0


def _frame(payload: dict) -> bytes:
    import msgpack

    packed = msgpack.packb(payload)
    return len(packed).to_bytes(4, "big") + packed


@pytest.mark.asyncio
async def test_stream_yields_msgpack_frames(tmp_path):
    frames = _frame({"event_type": "intermediate", "samp_ix": 0, "step_ix": 3, "image": b"prev"}) + _frame(
        {"event_type": "final", "samp_ix": 0, "image": b"RIFF....WEBP"}
    )
    # split across chunks on purpose, including inside a frame
    chunks = [frames[:7], frames[7:30], frames[30:]]

    async def aiter_content():
        for c in chunks:
            yield c

    response = mock.Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/octet-stream"}
    response.aiter_content = aiter_content
    session = _session(response)
    limiter = DailyImageLimiter(5, state_file=tmp_path / "s.json")
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)

    events = [e async for e in gen.request_stream(session, limiter=limiter)]
    assert [e.event_type for e in events] == ["intermediate", "final"]
    assert events[0].step_ix == 3 and events[0].image == b"prev"
    assert events[1].is_final and events[1].image == b"RIFF....WEBP"
    assert limiter.used == 1
    call = session.post.await_args
    assert call.args[0].endswith("/ai/generate-image-stream")
    assert call.kwargs["stream"] is True
    payload = json.loads(call.kwargs["data"].split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n--", 1)[0])
    assert payload["parameters"]["stream"] == "msgpack"


@pytest.mark.asyncio
async def test_stream_counts_a_final_image_even_if_the_caller_stops(tmp_path, monkeypatch):
    frames = _frame({"event_type": "final", "samp_ix": 0, "image": b"a"}) + _frame(
        {"event_type": "final", "samp_ix": 1, "image": b"b"}
    )

    async def aiter_content():
        yield frames

    response = mock.Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/octet-stream"}
    response.aiter_content = aiter_content
    limiter = DailyImageLimiter(5, state_file=tmp_path / "s.json")
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    async for event in gen.request_stream(_session(response), limiter=limiter):
        assert event.is_final
        break
    assert limiter.used == 1


@pytest.mark.asyncio
async def test_no_limiter_unless_asked(tmp_path, monkeypatch):
    from novelai_python.utils import daily_limit

    monkeypatch.setenv(daily_limit.ENV_STATE_FILE, str(tmp_path / "default.json"))
    monkeypatch.setattr(daily_limit, "_default_limiter", daily_limit._UNSET)
    response = mock.Mock()
    response.headers = {"Content-Type": "image/webp"}
    response.status_code = 200
    response.content = b"RIFF\x00\x00\x00\x00WEBPVP8 "
    await GenerateImageInfer.build_generate("1girl").request(_session(response))
    assert daily_limit._default_limiter is daily_limit._UNSET
    assert not (tmp_path / "default.json").exists()


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


@pytest.mark.asyncio
async def test_stream_error_keeps_the_server_message():
    body = b'{"statusCode": 402, "message": "Insufficient Anlas"}'
    response = mock.Mock()
    response.status_code = 402
    response.headers = {"Content-Type": "application/json"}
    response.content = b""  # nothing is read yet on a stream=True response
    response.json = mock.Mock(side_effect=ValueError("empty"))
    response.acontent = mock.AsyncMock(return_value=body)
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    with pytest.raises(AuthError) as e:
        async for _ in gen.request_stream(_session(response)):
            pass
    assert e.value.message == "Insufficient Anlas"
    assert e.value.code == 402
