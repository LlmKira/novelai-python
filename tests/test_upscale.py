# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午12:03
# @Author  : sudoskys
# @File    : test_upscale.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
# @Time    : 2024/2/14 下午4:20
# @Author  : sudoskys
# @File    : test_upscale.py
# @Software: PyCharm
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import APIError, Upscale, AuthError


@pytest.mark.asyncio
async def test_validation_error_during_upscale():
    validation_error_response = mock.Mock()
    validation_error_response.headers = {"Content-Type": "application/json"}
    validation_error_response.status_code = 400
    validation_error_response.json.return_value = {
        "statusCode": 400,
        "message": "A validation error occurred."
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=validation_error_response)
    session.headers = {}

    upscale = Upscale(image="base64_encoded_image", height=100, width=100)
    with pytest.raises(AuthError) as e:
        await upscale.request(session=session)
    assert e.type is AuthError
    expected_message = 'A validation error occurred.'
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_unauthorized_error_during_upscale():
    unauthorized_error_response = mock.Mock()
    unauthorized_error_response.headers = {"Content-Type": "application/json"}
    unauthorized_error_response.status_code = 401
    unauthorized_error_response.json.return_value = {
        "statusCode": 401,
        "message": "Unauthorized."
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=unauthorized_error_response)
    session.headers = {}

    upscale = Upscale(image="base64_encoded_image", height=100, width=100)
    with pytest.raises(APIError) as e:
        await upscale.request(session=session)
    assert e.type is AuthError
    expected_message = 'Unauthorized.'
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_unknown_error_during_upscale():
    unknown_error_response = mock.Mock()
    unknown_error_response.headers = {"Content-Type": "application/json"}
    unknown_error_response.status_code = 500
    unknown_error_response.json.return_value = {
        "statusCode": 500,
        "message": "Unknown error occurred."
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=unknown_error_response)
    session.headers = {}

    upscale = Upscale(image="base64_encoded_image", height=100, width=100)
    with pytest.raises(APIError) as e:
        await upscale.request(session=session)
    expected_message = 'Unknown error occurred.'
    assert expected_message == str(e.value)
