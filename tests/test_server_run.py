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


@patch("novelai_python.server.Subscription")
def test_bearer_prefix_is_not_sent_twice(mock_subscription):
    from novelai_python.server import session

    seen = []

    async def record(*args, session=None, **kwargs):
        seen.append(session.jwt_token.get_secret_value())
        raise RuntimeError("stop")

    mock_subscription.return_value.request = record
    TestClient(app, raise_server_exceptions=False).get("/user/subscription", headers={"Authorization": "Bearer pst-a"})
    TestClient(app, raise_server_exceptions=False).get("/user/subscription", headers={"Authorization": "pst-b"})
    assert seen == ["pst-a", "pst-b"]
    session.clear()


def test_stream_error_before_the_first_event_keeps_its_status(monkeypatch):
    from novelai_python import AuthError, LLMStream
    from novelai_python.sdk.ai import generate

    class FakeTokenizer:
        def encode(self, text):
            return [1, 2]

        def total_tokens(self):
            return 128256

    monkeypatch.setattr(generate, "get_tokenizer", lambda name: FakeTokenizer())

    async def fail(self, session, **kwargs):
        raise AuthError("bad token", request={}, response={}, code=401)
        yield  # an async generator, like LLMStream.request

    monkeypatch.setattr(LLMStream, "request", fail)
    response = client.post(
        "/ai/generate-stream",
        json={"input": "hi", "model": "llama-3-erato-v1"},
        headers={"Authorization": "Bearer x"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "bad token"


def test_voice_without_seed_is_a_validation_error():
    response = client.get("/ai/generate-voice", params={"text": "hi"}, headers={"Authorization": "Bearer x"})
    assert response.status_code == 422


@patch("novelai_python.server.AugmentImageInfer")
def test_augment_image_reads_the_image_from_the_body(mock_augment):
    async def stop(*args, **kwargs):
        raise RuntimeError("stop")

    mock_augment.build.return_value.request = stop
    TestClient(app, raise_server_exceptions=False).post(
        "/ai/augment-image",
        params={"req_type": "bg-removal"},
        content=b"\x89PNG image bytes",
        headers={"Authorization": "Bearer x", "Content-Type": "application/octet-stream"},
    )
    assert mock_augment.build.call_args.kwargs["image"] == b"\x89PNG image bytes"
