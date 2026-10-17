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
    client = TestClient(app)
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
