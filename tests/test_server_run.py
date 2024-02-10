# -*- coding: utf-8 -*-
# @Time    : 2024/1/30 下午11:52
# @Author  : sudoskys
# @File    : test_server_run.py
# @Software: PyCharm

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.novelai_python.server import app, get_session

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch('src.novelai_python.server.Subscription')
def test_subscription_without_api_key(mock_subscription):
    mock_subscription.return_value.request.return_value.model_dump.return_value = {"status": "subscribed"}
    response = client.get("/user/subscription")
    assert response.status_code == 403


@patch('src.novelai_python.server.GenerateImageInfer')
def test_generate_image_without_api_key(mock_generate_image):
    mock_generate_image.return_value.request.return_value = {"status": "image generated"}
    response = client.post("/ai/generate_image")
    assert response.status_code == 403


def test_get_session_new_token():
    token = "new_token"
    session = get_session(token)
    assert session.jwt_token.get_secret_value() == token


def test_get_session_existing_token():
    token = "existing_token"
    get_session(token)
    session = get_session(token)
    assert session.jwt_token.get_secret_value() == token
