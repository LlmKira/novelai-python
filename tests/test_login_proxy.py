from unittest import mock

import pytest

from novelai_python import ApiCredential, APIError, Login
from novelai_python.sdk.user import login as login_module

PROXY = "http://user:pass@127.0.0.1:18080"


def _fake_session_class(status=201, body=b'{"accessToken": "t"}'):
    created: list[dict] = []

    class FakeSession:
        def __init__(self, **kwargs):
            created.append(kwargs)
            self.headers = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return None

        async def post(self, *args, **kwargs):
            response = mock.Mock()
            response.status_code = status
            response.headers = {"Content-Type": "application/json"}
            response.content = body
            return response

    return FakeSession, created


def test_login_session_uses_its_proxy():
    session = Login.build(user_name="a@b.c", password="pw", proxy=PROXY).session
    assert session.proxies == {"http": PROXY, "https": PROXY}


@pytest.mark.asyncio
async def test_login_request_takes_the_credential_proxy(monkeypatch):
    fake, created = _fake_session_class()
    monkeypatch.setattr(login_module, "AsyncSession", fake)
    credential = ApiCredential(api_token="pst-x", proxy=PROXY)
    await Login.build(user_name="a@b.c", password="pw").request(credential)
    assert created[0]["proxies"] == {"http": PROXY, "https": PROXY}
    assert created[0]["trust_env"] is False


@pytest.mark.asyncio
async def test_login_error_does_not_carry_the_access_key(monkeypatch):
    fake, _ = _fake_session_class(status=401, body=b'{"statusCode": 401, "message": "bad key"}')
    monkeypatch.setattr(login_module, "AsyncSession", fake)
    login = Login.build(user_name="a@b.c", password="pw")
    with pytest.raises(APIError) as e:
        await login.request()
    assert login.key not in str(e.value.__dict__)


def test_jwt_credential_accepts_no_token():
    from novelai_python import JwtCredential

    assert JwtCredential(jwt_token=None).jwt_token is None


@pytest.mark.asyncio
async def test_bearer_credentials_share_the_session_setup():
    from novelai_python import JwtCredential

    for credential in (ApiCredential(api_token="pst-a", proxy=PROXY), JwtCredential(jwt_token="eyB", proxy=PROXY)):
        session = await credential.get_session()
        assert session.headers["authorization"].startswith("Bearer ")
        assert session.proxies == {"http": PROXY, "https": PROXY}
        await session.close()
