# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午3:17
# @Author  : sudoskys
# @File    : test_information.py
# @Software: PyCharm
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import Information, InformationResp, AuthError, APIError


def test_endpoint_setter():
    info = Information()
    assert info.endpoint == "https://api.novelai.net"
    new_endpoint = "https://api.testai.net"
    info.endpoint = new_endpoint
    assert info.endpoint == new_endpoint


@pytest.mark.asyncio
async def test_request_method_successful():
    successful_response = mock.Mock()
    successful_response.headers = {"Content-Type": "application/json"}
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "emailVerified": True,
        "emailVerificationLetterSent": True,
        "trialActivated": True,
        "trialActionsLeft": 0,
        "trialImagesLeft": 0,
        "accountCreatedAt": 0
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=successful_response)
    session.headers = {}

    info = Information()
    resp = await info.request(session)
    assert isinstance(resp, InformationResp)


@pytest.mark.asyncio
async def test_request_method_unauthorized_error():
    auth_response = mock.Mock()
    auth_response.headers = {"Content-Type": "application/json"}
    auth_response.status_code = 401
    auth_response.json.return_value = {"statusCode": 401, "message": "Access Token is incorrect."}

    session = mock.MagicMock(spec=AsyncSession)
    session.headers = {}
    session.get = mock.AsyncMock(return_value=auth_response)

    info = Information()
    with pytest.raises(AuthError) as e:
        await info.request(session)
    assert e.type is AuthError
    expected_message = 'Access Token is incorrect.'
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_request_method_unknown_error():
    unknown_error_response = mock.Mock()
    unknown_error_response.headers = {"Content-Type": "application/json"}
    unknown_error_response.status_code = 500
    unknown_error_response.json.return_value = {"statusCode": 500, "message": "An unknown error occurred."}

    session = mock.MagicMock(spec=AsyncSession)
    session.headers = {}
    session.get = mock.AsyncMock(return_value=unknown_error_response)

    info = Information()
    with pytest.raises(APIError) as e:
        await info.request(session)
    expected_message = 'An unknown error occurred.'
    assert expected_message == str(e.value)
