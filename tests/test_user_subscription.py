# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:31
# @Author  : sudoskys
# @File    : test_subscription.py
# @Software: PyCharm
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import APIError, Subscription, SubscriptionResp, AuthError


@pytest.mark.asyncio
async def test_successful_subscription_request():
    successful_response = mock.Mock()
    successful_response.headers = {"Content-Type": "application/json"}
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "tier": 3,
        "active": True,
        "expiresAt": 1708646400,
        "perks": {
            "maxPriorityActions": 1000,
            "startPriority": 10,
            "moduleTrainingSteps": 10000,
            "unlimitedMaxPriority": True,
            "voiceGeneration": True,
            "imageGeneration": True,
            "unlimitedImageGeneration": True,
            "unlimitedImageGenerationLimits": [
                {
                    "resolution": 4194304,
                    "maxPrompts": 0
                },
                {
                    "resolution": 1048576,
                    "maxPrompts": 1
                }
            ],
            "contextTokens": 8192
        },
        "paymentProcessorData": None,
        "trainingStepsLeft": {
            "fixedTrainingStepsLeft": 8825,
            "purchasedTrainingSteps": 0
        },
        "accountType": 0
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=successful_response)
    session.headers = {}

    subscription = Subscription()
    resp = await subscription.request(session)
    assert isinstance(resp, SubscriptionResp)


@pytest.mark.asyncio
async def test_incorrect_access_token_subscription_request():
    incorrect_token_response = mock.Mock()
    incorrect_token_response.headers = {"Content-Type": "application/json"}
    incorrect_token_response.status_code = 401
    incorrect_token_response.json.return_value = {
        "statusCode": 401,
        "message": "Access Token is incorrect."
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=incorrect_token_response)
    session.headers = {}

    subscription = Subscription()
    with pytest.raises(AuthError) as e:
        await subscription.request(session)
    assert e.type is AuthError
    expected_message = 'Access Token is incorrect.'
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_unknown_error_subscription_request():
    unknown_error_response = mock.Mock()
    unknown_error_response.headers = {"Content-Type": "application/json"}
    unknown_error_response.status_code = 500
    unknown_error_response.json.return_value = {
        "statusCode": 500,
        "message": "An unknown error occurred."
    }
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=unknown_error_response)
    session.headers = {}

    subscription = Subscription()
    with pytest.raises(APIError) as e:
        await subscription.request(session)
    assert e.type is APIError
    expected_message = 'An unknown error occurred.'
    assert expected_message == str(e.value)
