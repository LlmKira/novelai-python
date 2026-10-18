# @Time    : 2024/1/30 下午11:52
# @Author  : sudoskys
# @File    : test_server_run.py


from unittest.mock import patch

from fastapi.testclient import TestClient

from novelai_python.server import app, get_session

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("novelai_python.server.Subscription")
def test_subscription_without_api_key(mock_subscription):
    mock_subscription.return_value.request.return_value.model_dump.return_value = {"status": "subscribed"}
    response = client.get("/user/subscription")
    assert response.status_code == 401  # FastAPI >=0.120: missing bearer -> 401 (RFC 7235)


@patch("novelai_python.server.GenerateImageInfer")
def test_generate_image_without_api_key(mock_generate_image):
    mock_generate_image.return_value.request.return_value = {"status": "image generated"}
    response = client.post("/ai/generate-image")
    assert response.status_code == 401  # FastAPI >=0.120: missing bearer -> 401 (RFC 7235)


@patch("novelai_python.server.Subscription")
def test_subscription_keeps_the_upstream_status(mock_subscription):
    from novelai_python import AuthError

    async def fail(*args, **kwargs):
        raise AuthError("bad token", request={}, response={}, code=401)

    mock_subscription.return_value.request = fail
    response = client.get("/user/subscription", headers={"Authorization": "Bearer x"})
    assert response.status_code == 401
    assert response.json() == {"message": "bad token", "code": 401}


def test_session_cache_is_bounded():
    from novelai_python.server import SESSION_CACHE_LIMIT, session

    session.clear()
    for index in range(SESSION_CACHE_LIMIT + 10):
        get_session(f"token-{index}")
    assert len(session) == SESSION_CACHE_LIMIT
    assert "token-0" not in session
    session.clear()


def test_get_session_new_token():
    token = "new_token"
    session = get_session(token)
    assert session.jwt_token.get_secret_value() == token


def test_get_session_existing_token():
    token = "existing_token"
    get_session(token)
    session = get_session(token)
    assert session.jwt_token.get_secret_value() == token
