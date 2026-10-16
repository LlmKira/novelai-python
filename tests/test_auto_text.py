import json
import random
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import GenerateImageInfer, Login
from novelai_python.sdk.ai._enum import Model
from novelai_python.sdk.ai.generate_image import Character, PositionMap
from novelai_python.sdk.ai.generate_image.auto_text import _quoted_texts, apply_auto_text, strip_auto_text
from novelai_python.tool.random_prompt.generate_scene_composition import Conditions, select_weighted_option

Q = ", very aesthetic, masterpiece, no text"


# --- auto text block (ported from the web client) ---


def test_example_from_web_client_japanese():
    p = '1girl, cyberpunk, looking aside, "ホテル" ' + Q
    assert apply_auto_text(p) == '1girl, cyberpunk, looking aside, "ホテル" ' + Q + ", teXt: ホテル"


def test_user_text_block_wins_and_idempotent():
    p = 'sign "hi"' + Q + ", text: hello"
    assert apply_auto_text(p) == p
    once = apply_auto_text('sign "hi"' + Q)
    assert apply_auto_text(once) == once  # teXt: counts as text:


def test_apostrophes_are_not_quotes():
    assert apply_auto_text("girl's room, it's cozy" + Q) == "girl's room, it's cozy" + Q
    assert _quoted_texts("say 'hello world' now") == ["hello world"]
    assert _quoted_texts("“A”, 「B」") == ["A", "B"]


def test_character_texts_ordered_by_position():
    chars = [
        {"prompt": 'boy says "right"', "center": {"x": 0.9, "y": 0.5}},
        {"prompt": 'girl says "left"', "center": {"x": 0.1, "y": 0.5}},
    ]
    assert apply_auto_text("2people" + Q, chars, True).endswith("teXt: left\n\nright")


def test_strip_only_web_client_block():
    auto = apply_auto_text('a "X"' + Q)
    assert strip_auto_text(auto) == 'a "X"' + Q
    manual = 'a "X"' + Q + ", teXt: something else"
    assert strip_auto_text(manual) == manual


def test_generation_puts_text_block_after_quality_suffix():
    gen = GenerateImageInfer.build_generate('girl holding a sign, "Hello"', model=Model.NAI_DIFFUSION_5_FULL)
    assert gen.input == 'girl holding a sign, "Hello"' + Q + ", teXt: Hello"
    assert gen.parameters.v4_prompt is not None
    assert gen.parameters.v4_prompt.caption.base_caption == gen.input


def test_generation_collects_character_texts():
    chars = [Character.build(prompt='girl, shouting "Run!"', center=PositionMap.AUTO)]
    gen = GenerateImageInfer.build_generate("1girl, street", model=Model.NAI_DIFFUSION_5_FULL, character_prompts=chars)
    assert gen.input.endswith(", teXt: Run!")


def test_auto_text_only_on_v5_and_can_be_turned_off():
    v45 = GenerateImageInfer.build_generate('sign, "Hello"', model=Model.NAI_DIFFUSION_4_5_FULL)
    assert "teXt:" not in v45.input
    gen = GenerateImageInfer.build_generate('sign, "Hello"', model=Model.NAI_DIFFUSION_5_FULL)
    off = GenerateImageInfer(
        input='sign, "Hello"', model=Model.NAI_DIFFUSION_5_FULL, parameters=gen.parameters, auto_text=False
    )
    assert "teXt:" not in off.input
    assert "auto_text" not in off.model_dump(mode="json")


# --- random prompt selector: exclusions and requirements (web client LR) ---


def test_selector_respects_requirements_and_exclusions():
    table = [
        ["shortstack", 12, [], ["female"], []],
        ["ugly man", 12, [], ["male"], []],
        ["hat", 12, ["headcovering"], [], ["no hat"]],
    ]
    random.seed(0)
    for _ in range(200):
        picked = select_weighted_option(table, Conditions(tags=["female", "no hat"]))
        assert picked == "shortstack"
    for _ in range(200):
        assert select_weighted_option(table, Conditions(tags=["male"])) in ("ugly man", "hat")


# --- login request as the web client sends it ---


def _session(response):
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=response)
    session.headers = {}
    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)
    return session


def _login_response():
    response = mock.Mock()
    response.status_code = 201
    response.headers = {"Content-Type": "application/json"}
    response.content = json.dumps({"accessToken": "jwt"}).encode()
    return response


@pytest.mark.asyncio
async def test_login_sends_browser_headers_without_made_up_measure_id():
    session = _session(_login_response())
    await Login.build(user_name="a@b.c", password="pw").request(session)
    kwargs = session.post.await_args.kwargs
    assert set(kwargs["headers"]) == {"x-correlation-id", "x-initiated-at"}
    assert len(kwargs["headers"]["x-correlation-id"]) == 6
    assert json.loads(kwargs["data"]) == {"key": Login.build(user_name="a@b.c", password="pw").key}


@pytest.mark.asyncio
async def test_login_passes_browser_measure_id_and_recaptcha():
    session = _session(_login_response())
    await Login.build(user_name="a@b.c", password="pw", recaptcha="rc", measure_id="1792188383068.OuQYKK").request(
        session
    )
    kwargs = session.post.await_args.kwargs
    assert kwargs["headers"]["x-measure-id"] == "1792188383068.OuQYKK"
    body = json.loads(kwargs["data"])
    assert body["recaptcha"] == "rc" and "measure_id" not in body
