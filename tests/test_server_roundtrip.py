"""A request built on the client and posted to the server must reach NovelAI unchanged."""

import pytest
from fastapi.testclient import TestClient

from novelai_python import GenerateImageInfer
from novelai_python.sdk.ai._enum import Model
from novelai_python.sdk.ai.generate_image import CharacterReference
from novelai_python.server import app

PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


@pytest.fixture
def forwarded(monkeypatch):
    seen: list[GenerateImageInfer] = []

    async def fake_request(self, *args, **kwargs):
        seen.append(self)
        raise RuntimeError("stop before the network")

    monkeypatch.setattr(GenerateImageInfer, "request", fake_request)
    return seen


def _post(body: str):
    # The fake request raises to stop before the network; the app's exception handler
    # turns that into a 500, and TestClient must not re-raise for the test to inspect it.
    client = TestClient(app, raise_server_exceptions=False)
    return client.post(
        "/ai/generate-image",
        content=body,
        headers={"Authorization": "Bearer pst-test", "Content-Type": "application/json"},
    )


@pytest.mark.parametrize("model", [Model.NAI_DIFFUSION_5_FULL, Model.NAI_DIFFUSION_4_5_FULL, Model.NAI_DIFFUSION_3])
def test_prompt_and_negative_are_not_enhanced_twice(forwarded, model):
    client_side = GenerateImageInfer.build_generate("1girl, smile", model=model, ucPreset=0)
    _post(client_side.model_dump_json())
    server_side = forwarded[0]
    assert server_side.model == model
    assert server_side.input == client_side.input
    assert server_side.parameters.negative_prompt == client_side.parameters.negative_prompt


def test_character_reference_survives_the_server(forwarded):
    client_side = GenerateImageInfer.build_generate(
        "1girl",
        model=Model.NAI_DIFFUSION_4_5_FULL,
        character_references=[CharacterReference(image=PNG_1X1)],
    )
    response = _post(client_side.model_dump_json())
    assert response.status_code != 422, response.text
    assert forwarded[0].model == Model.NAI_DIFFUSION_4_5_FULL
    assert forwarded[0].parameters.director_reference_images


def _png_b64(size=(832, 1216), color="black") -> str:
    import base64
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_infill_and_img2img_keep_their_action(forwarded):
    infill = GenerateImageInfer.build_infill(
        "1girl", model=Model.NAI_DIFFUSION_4_5_FULL, image=_png_b64(), mask=_png_b64(color="white")
    )
    _post(infill.model_dump_json())
    assert forwarded[-1].action == infill.action
    assert forwarded[-1].parameters.mask

    img2img = GenerateImageInfer.build_img2img("1girl", model=Model.NAI_DIFFUSION_4_5_FULL, image=_png_b64(), seed=7)
    _post(img2img.model_dump_json())
    sent = forwarded[-1].parameters
    assert forwarded[-1].action == img2img.action
    assert (sent.color_correct, sent.extra_noise_seed) == (img2img.parameters.color_correct, 7)


def test_auto_text_off_survives_the_server(forwarded):
    params = GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL).parameters
    client_side = GenerateImageInfer(
        input='1girl, holding a sign, "hello"', model=Model.NAI_DIFFUSION_5_FULL, parameters=params, auto_text=False
    )
    assert "teXt:" not in client_side.input
    _post(client_side.model_dump_json())
    assert forwarded[-1].auto_text is False
    assert "teXt:" not in forwarded[-1].input
    assert "auto_text" not in forwarded[-1]._build_body(stream=False)[0]


def test_characters_without_positions_keep_use_coords_off(forwarded):
    from novelai_python.sdk.ai.generate_image import Character

    client_side = GenerateImageInfer.build_generate(
        "2girls",
        model=Model.NAI_DIFFUSION_4_5_FULL,
        character_prompts=[Character(prompt="girl, red hair"), Character(prompt="girl, blue hair")],
    )
    assert client_side.parameters.use_coords is False
    _post(client_side.model_dump_json())
    assert forwarded[-1].parameters.use_coords is False
    assert forwarded[-1].parameters.v4_prompt.use_coords is False
