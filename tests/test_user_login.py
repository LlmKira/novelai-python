# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:20
# @Author  : sudoskys
# @File    : test_login.py
# @Software: PyCharm
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import APIError, Login, LoginResp


@pytest.mark.asyncio
async def test_successful_user_login():
    successful_login_response = mock.Mock()
    successful_login_response.headers = {"Content-Type": "application/json"}
    successful_login_response.status_code = 201
    successful_login_response.json.return_value = {
        "accessToken": "string"
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=successful_login_response)
    session.headers = {}

    login = Login(key="encoded_key")
    login.session = session
    resp = await login.request()
    assert isinstance(resp, LoginResp)
    assert resp.accessToken == "string"


@pytest.mark.asyncio
async def test_validation_error_during_login():
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

    login = Login(key="encoded_key")
    login.session = session
    with pytest.raises(APIError) as e:
        await login.request()
    assert e.type is APIError
    expected_message = 'A validation error occurred.'
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_incorrect_access_key_during_login():
    incorrect_key_response = mock.Mock()
    incorrect_key_response.headers = {"Content-Type": "application/json"}
    incorrect_key_response.status_code = 401
    incorrect_key_response.json.return_value = {
        "statusCode": 401,
        "message": "Access Key is incorrect."
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=incorrect_key_response)
    session.headers = {}

    login = Login(key="encoded_key")
    login.session = session
    with pytest.raises(APIError) as e:
        await login.request()
    assert e.type is APIError
    expected_message = 'Access Key is incorrect.'
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_unknown_error_during_login():
    unknown_error_response = mock.Mock()
    unknown_error_response.headers = {"Content-Type": "application/json"}
    unknown_error_response.status_code = 500
    unknown_error_response.json.return_value = {
        "statusCode": 500,
        "message": "key must be longer than or equal to 64 characters"
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.post = mock.AsyncMock(return_value=unknown_error_response)
    session.headers = {}

    login = Login(key="encoded_key")
    login.session = session
    with pytest.raises(APIError) as e:
        await login.request()
    expected_message = 'key must be longer than or equal to 64 characters'
    assert expected_message == str(e.value)
