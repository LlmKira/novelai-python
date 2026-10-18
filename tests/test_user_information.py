import json

# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午3:17
# @Author  : sudoskys
# @File    : test_information.py
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import APIError, AuthError, Information, InformationResp


def set_json(resp, payload):
    """Mock a JSON body the way the SDK reads it (raw bytes) and via .json()."""
    resp.json = mock.Mock(return_value=payload)
    resp.content = json.dumps(payload).encode()


def test_endpoint_setter():
    info = Information()
    # api.novelai.net tells third-party clients to "update to the image URL"
    assert info.endpoint == "https://image.novelai.net"
    new_endpoint = "https://api.testai.net"
    info.endpoint = new_endpoint
    assert info.endpoint == new_endpoint


@pytest.mark.asyncio
async def test_request_method_successful():
    successful_response = mock.Mock()
    successful_response.headers = {"Content-Type": "application/json"}
    successful_response.status_code = 200
    set_json(
        successful_response,
        {
            "emailVerified": True,
            "emailVerificationLetterSent": True,
            "trialActivated": True,
            "trialActionsLeft": 0,
            "trialImagesLeft": 0,
            "accountCreatedAt": 0,
        },
    )
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=successful_response)
    session.request = session.get
    session.headers = {}

    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)

    info = Information()
    resp = await info.request(session)
    assert isinstance(resp, InformationResp)


@pytest.mark.asyncio
async def test_request_method_unauthorized_error():
    auth_response = mock.Mock()
    auth_response.headers = {"Content-Type": "application/json"}
    auth_response.status_code = 401
    set_json(auth_response, {"statusCode": 401, "message": "Access Token is incorrect."})

    session = mock.MagicMock(spec=AsyncSession)
    session.headers = {}
    session.get = mock.AsyncMock(return_value=auth_response)
    session.request = session.get

    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)

    info = Information()
    with pytest.raises(AuthError) as e:
        await info.request(session)
    assert e.type is AuthError
    expected_message = "Access Token is incorrect."
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_request_method_unknown_error():
    unknown_error_response = mock.Mock()
    unknown_error_response.headers = {"Content-Type": "application/json"}
    unknown_error_response.status_code = 500
    set_json(unknown_error_response, {"statusCode": 500, "message": "An unknown error occurred."})

    session = mock.MagicMock(spec=AsyncSession)
    session.headers = {}
    session.get = mock.AsyncMock(return_value=unknown_error_response)
    session.request = session.get

    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)

    info = Information()
    with pytest.raises(APIError) as e:
        await info.request(session)
    expected_message = "An unknown error occurred."
    assert expected_message == str(e.value)
