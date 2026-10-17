# Offline tests for the endpoints and request fields added from the official API spec
# (image/text.novelai.net/docs/doc.json, 2026-10) and the web client bundle.
import base64
import io
import json
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession
from PIL import Image

from novelai_python import (
    APIError,
    AuthError,
    CharacterReference,
    CreatePersistentToken,
    EncodeVibe,
    GenerateImageInfer,
    OAIChatCompletion,
    OAIChatMessage,
    OAIModels,
    OAITokenCount,
    Priority,
)
from novelai_python._response.user.subscription import SubscriptionUsage
from novelai_python.sdk.ai._enum import Model
from novelai_python.sdk.ai.generate_image import Character


def _response(status=200, content=b"{}", content_type="application/json"):
    response = mock.Mock()
    response.status_code = status
    response.content = content
    response.headers = {"Content-Type": content_type}
    response.json = lambda: json.loads(content)
    return response


def _session(response):
    session = mock.MagicMock(spec=AsyncSession)
    session.request = mock.AsyncMock(return_value=response)
    session.post = mock.AsyncMock(return_value=response)
    session.headers = {}
    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)
    return session


def _png(width, height, color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, "PNG")
    return buf.getvalue()


# --- transparent background (V5) ---


def test_transparent_background_goes_before_quality_suffix():
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL, transparent_background=True)
    assert gen.input == "1girl, transparent background, very aesthetic, masterpiece, no text"
    assert gen.parameters.straight_alpha is True
    assert gen.parameters.tag_hint_transparent_background is True


def test_transparent_background_without_quality_tags():
    gen = GenerateImageInfer.build_generate(
        "1girl", model=Model.NAI_DIFFUSION_5_FULL, transparent_background=True, qualityToggle=False
    )
    assert gen.input == "1girl, transparent background"


def test_transparent_background_not_duplicated():
    gen = GenerateImageInfer.build_generate(
        "1girl, transparent background", model=Model.NAI_DIFFUSION_5_FULL, transparent_background=True
    )
    assert gen.input.count("transparent background") == 1


def test_transparent_background_ignored_before_v5():
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_4_5_FULL, transparent_background=True)
    assert "transparent background" not in gen.input


# --- character limit per model ---


def test_v5_takes_up_to_32_characters():
    chars = [Character.build(prompt=f"girl {i}") for i in range(32)]
    gen = GenerateImageInfer.build_generate("2girls", model=Model.NAI_DIFFUSION_5_FULL, character_prompts=chars)
    assert len(gen.parameters.characterPrompts) == 32


def test_v45_rejects_seventh_character():
    chars = [Character.build(prompt=f"girl {i}") for i in range(7)]
    with pytest.raises(ValueError, match="at most 6"):
        GenerateImageInfer.build_generate("2girls", model=Model.NAI_DIFFUSION_4_5_FULL, character_prompts=chars)


# --- error frame inside the image stream ---


def _frame(payload: dict) -> bytes:
    import msgpack

    packed = msgpack.packb(payload)
    return len(packed).to_bytes(4, "big") + packed


@pytest.mark.asyncio
async def test_stream_error_frame_raises():
    body = _frame({"event_type": "intermediate", "samp_ix": 0, "step_ix": 1, "image": b"p"}) + _frame(
        {"event_type": "error", "code": 500, "message": "Error generating image, an internal error occurred"}
    )

    async def aiter_content():
        yield body

    response = _response(content_type="application/octet-stream")
    response.aiter_content = aiter_content
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL)
    events = []
    with pytest.raises(APIError) as err:
        async for event in gen.request_stream(_session(response), limiter=False):
            events.append(event)
    assert [e.event_type for e in events] == ["intermediate"]
    assert err.value.code == 500
    assert "internal error" in str(err.value)


# --- character reference (V4.5) ---


def test_character_reference_fields_match_web_client():
    refs = [
        CharacterReference(image=_png(300, 600)),
        CharacterReference(image=_png(800, 400), description="style", strength=0.5, fidelity=0.75),
    ]
    gen = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_4_5_FULL, character_references=refs)
    p = gen.parameters.model_dump(mode="json", exclude_none=True)
    assert p["director_reference_descriptions"] == [
        {"caption": {"base_caption": "character&style", "char_captions": []}, "legacy_uc": False},
        {"caption": {"base_caption": "style", "char_captions": []}, "legacy_uc": False},
    ]
    assert p["director_reference_strength_values"] == [1.0, 0.5]
    assert p["director_reference_secondary_strength_values"] == [0.0, 0.25]
    assert p["director_reference_information_extracted"] == [1.0, 1.0]
    sizes = [Image.open(io.BytesIO(base64.b64decode(b))).size for b in p["director_reference_images"]]
    assert sizes == [(1024, 1536), (1536, 1024)]
    # padding is opaque black, the picture stays centred
    portrait = Image.open(io.BytesIO(base64.b64decode(p["director_reference_images"][0]))).convert("RGB")
    assert portrait.getpixel((0, 768)) == (0, 0, 0)
    assert portrait.getpixel((512, 768)) == (255, 0, 0)


def test_character_reference_rejected_on_v5():
    with pytest.raises(ValueError, match=r"V4.5"):
        GenerateImageInfer.build_generate(
            "1girl", model=Model.NAI_DIFFUSION_5_FULL, character_references=[CharacterReference(image=_png(64, 64))]
        )


# --- usage limit ---


def test_usage_reads_purchased_percent():
    usage = SubscriptionUsage.model_validate(
        {"percent": 40, "purchasedPercent": 120, "isNegative": False, "timeUntilNextPercent": 0}
    )
    assert usage.purchasedPercent == 120
    assert usage.refill_percent_per_day is None  # 0 = refill paused above the cap


# --- simple JSON endpoints ---


@pytest.mark.asyncio
async def test_priority():
    session = _session(_response(content=b'{"maxPriorityActions":10,"nextRefillAt":1792200000,"taskPriority":2.5}'))
    resp = await Priority().request(session)
    assert resp.taskPriority == 2.5 and resp.maxPriorityActions == 10
    method, url = session.request.await_args.args
    assert (method, url) == ("GET", "https://image.novelai.net/user/priority")


@pytest.mark.asyncio
async def test_create_persistent_token_and_conflict():
    session = _session(_response(status=201, content=b'{"token":"pst-abc"}'))
    resp = await CreatePersistentToken(overwrite=True).request(session)
    assert resp.token == "pst-abc"
    assert session.request.await_args.kwargs["json"] == {"overwrite": True}

    conflict = _session(_response(status=409, content=b'{"statusCode":409,"message":"Token already exists"}'))
    with pytest.raises(APIError) as err:
        await CreatePersistentToken().request(conflict)
    assert err.value.code == 409


@pytest.mark.asyncio
async def test_error_mapping_401_is_auth_error():
    session = _session(_response(status=401, content=b'{"statusCode":401,"message":"Access Token is incorrect."}'))
    with pytest.raises(AuthError):
        await Priority().request(session)


@pytest.mark.asyncio
async def test_encode_vibe():
    session = _session(_response(status=201, content=b"\x00vibe-binary", content_type="application/binary"))
    resp = await EncodeVibe(image=_png(64, 64), information_extracted=0.7).request(session)
    assert resp.vibe == b"\x00vibe-binary"
    assert resp.vibe_b64 == base64.b64encode(b"\x00vibe-binary").decode()
    method, url = session.request.await_args.args
    assert (method, url) == ("POST", "https://image.novelai.net/ai/encode-vibe")
    body = session.request.await_args.kwargs["json"]
    assert body["model"] == "nai-diffusion-4-5-full" and body["information_extracted"] == 0.7
    assert base64.b64decode(body["image"]).startswith(b"\x89PNG")


def test_encode_vibe_rejects_v5():
    with pytest.raises(ValueError, match="encoded vibes"):
        EncodeVibe(image=_png(64, 64), model=Model.NAI_DIFFUSION_5_FULL)


# --- OpenAI-compatible text API ---


@pytest.mark.asyncio
async def test_oa_chat_completion():
    answer = {"choices": [{"message": {"role": "assistant", "content": "hi"}}]}
    session = _session(_response(content=json.dumps(answer).encode()))
    req = OAIChatCompletion(model="glm-4-6", messages=[OAIChatMessage(role="user", content="hello")], min_p=0.05)
    assert await req.request(session) == answer
    method, url = session.request.await_args.args
    assert (method, url) == ("POST", "https://text.novelai.net/oa/v1/chat/completions")
    body = session.request.await_args.kwargs["json"]
    assert body == {
        "model": "glm-4-6",
        "messages": [{"role": "user", "content": "hello"}],
        "min_p": 0.05,
        "stream": False,
    }


@pytest.mark.asyncio
async def test_oa_chat_stream_reads_sse_until_done():
    lines = [
        b'data: {"choices":[{"delta":{"content":"He"}}]}',
        b"",
        b'data: {"choices":[{"delta":{"content":"llo"}}]}',
        b"data: [DONE]",
        b'data: {"never": "read"}',
    ]

    async def aiter_lines():
        for line in lines:
            yield line

    response = _response(content_type="text/event-stream")
    response.aiter_lines = aiter_lines
    session = _session(response)
    req = OAIChatCompletion(model="glm-4-6", messages=[OAIChatMessage(role="user", content="hi")])
    chunks = [c async for c in req.stream(session)]
    assert "".join(c["choices"][0]["delta"]["content"] for c in chunks) == "Hello"
    assert session.post.await_args.kwargs["json"]["stream"] is True


@pytest.mark.asyncio
async def test_oa_models_and_token_count():
    session = _session(_response(content=b'{"object":"list","data":[{"id":"glm-4-6","object":"model"}]}'))
    models = await OAIModels().request(session)
    assert [m.id for m in models.data] == ["glm-4-6"]

    session = _session(_response(content=b'{"encoded":[1,2,3],"length":3}'))
    count = await OAITokenCount(model="glm-4-6", prompt="a b c").request(session)
    assert count.length == 3 and count.encoded == [1, 2, 3]


# --- shapes captured from the web client on 2026-10-17 (Opus account, Chrome 155) ---


def test_trial_status_current_shape():
    from novelai_python import TrialStatusResp

    resp = TrialStatusResp.model_validate(
        {
            "used_text_actions": 0,
            "remaining_text_actions": 50,
            "used_image_actions": 8,
            "remaining_image_actions": 22,
            "eligible_for_text_gens": False,
            "eligible_for_image_gens": False,
            "trial_activated": True,
        }
    )
    assert resp.remaining_image_actions == 22 and resp.trial_activated is True


def test_user_endpoints_use_image_host():
    # api.novelai.net answers third-party clients "update to the image URL" (live 2026-10-17)
    from novelai_python import Information, Login, Subscription, Upscale

    for req in (Subscription(), Information(), Priority(), CreatePersistentToken()):
        assert req.base_url.startswith("https://image.novelai.net/user/")
    assert Login(key="x").base_url == "https://image.novelai.net/user/login"
    assert Upscale(image=_png(64, 64)).base_url == "https://image.novelai.net/ai/upscale"


def test_images_travel_as_form_parts():
    # the server reads image fields of a multipart request as form part names
    from novelai_python.sdk.ai.generate_image import split_image_parts

    img = base64.b64encode(_png(8, 8)).decode()
    vibe = base64.b64encode(b"vibe-bytes").decode()
    data = {
        "parameters": {
            "image": img,
            "reference_image_multiple": [vibe, vibe],
            "director_reference_images": [img],
        }
    }
    parts = split_image_parts(data)
    p = data["parameters"]
    assert p["image"] == "image" and len(p["image_cache_secret_key"]) == 64
    assert "reference_image_multiple" not in p and "director_reference_images" not in p
    assert [x["data"] for x in p["reference_image_multiple_cached"]] == ["ref_multiple_0", "ref_multiple_0"]
    # the same image is sent once: the director reference reuses the "image" part
    assert p["director_reference_images_cached"][0]["data"] == "image"
    assert [name for name, _ in parts] == ["image", "ref_multiple_0"]
    assert parts[1][1] == b"vibe-bytes"


@pytest.mark.asyncio
async def test_400_is_a_validation_error_on_the_newer_endpoints():
    from novelai_python import APIError, AuthError, EncodeVibe, OAITokenCount

    body = json.dumps({"statusCode": 400, "message": "bad input"}).encode()
    for request in (OAITokenCount(model="glm-4-6", prompt="x"), EncodeVibe(image=_png(8, 8))):
        response = mock.Mock()
        response.status_code = 400
        response.headers = {"Content-Type": "application/json"}
        response.content = body
        with pytest.raises(APIError) as e:
            await request.request(_session(response))
        assert not isinstance(e.value, AuthError)
        assert e.value.message == "bad input"
