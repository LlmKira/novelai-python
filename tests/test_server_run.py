# -*- coding: utf-8 -*-
# @Time    : 2024/1/30 下午11:52
# @Author  : sudoskys
# @File    : test_server_run.py
# @Software: PyCharm
from fastapi.testclient import TestClient

from src.novelai_python.sdk.ai.generate_image import GenerateImageInfer
from src.novelai_python.server import app, get_session

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_image_with_valid_token():
    valid_token = "valid_token"
    get_session(valid_token)  # to simulate a valid session
    response = client.post(
        "/ai/generate_image",
        headers={"Authorization": valid_token},
        json=GenerateImageInfer(input="1girl").model_dump()
    )
    assert response.status_code == 500
