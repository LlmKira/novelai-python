import json

# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:31
# @Author  : sudoskys
# @File    : test_subscription.py
from unittest import mock

import pytest
from curl_cffi.requests import AsyncSession

from novelai_python import APIError, AuthError, Subscription, SubscriptionResp


def set_json(resp, payload):
    """Mock a JSON body the way the SDK reads it (raw bytes) and via .json()."""
    resp.json = mock.Mock(return_value=payload)
    resp.content = json.dumps(payload).encode()


@pytest.mark.asyncio
async def test_successful_subscription_request():
    successful_response = mock.Mock()
    successful_response.headers = {"Content-Type": "application/json"}
    successful_response.status_code = 200
    set_json(
        successful_response,
        {
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
                    {"resolution": 4194304, "maxPrompts": 0},
                    {"resolution": 1048576, "maxPrompts": 1},
                ],
                "contextTokens": 8192,
            },
            "paymentProcessorData": None,
            "trainingStepsLeft": {"fixedTrainingStepsLeft": 8825, "purchasedTrainingSteps": 0},
            "accountType": 0,
        },
    )
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=successful_response)
    session.request = session.get
    session.headers = {}

    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)

    subscription = Subscription()
    resp = await subscription.request(session)
    assert isinstance(resp, SubscriptionResp)


@pytest.mark.asyncio
async def test_incorrect_access_token_subscription_request():
    incorrect_token_response = mock.Mock()
    incorrect_token_response.headers = {"Content-Type": "application/json"}
    incorrect_token_response.status_code = 401
    set_json(incorrect_token_response, {"statusCode": 401, "message": "Access Token is incorrect."})
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=incorrect_token_response)
    session.request = session.get
    session.headers = {}

    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)

    subscription = Subscription()
    with pytest.raises(AuthError) as e:
        await subscription.request(session)
    assert e.type is AuthError
    expected_message = "Access Token is incorrect."
    assert expected_message == str(e.value)


@pytest.mark.asyncio
async def test_unknown_error_subscription_request():
    unknown_error_response = mock.Mock()
    unknown_error_response.headers = {"Content-Type": "application/json"}
    unknown_error_response.status_code = 500
    set_json(unknown_error_response, {"statusCode": 500, "message": "An unknown error occurred."})
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=unknown_error_response)
    session.request = session.get
    session.headers = {}

    session.__aenter__ = mock.AsyncMock(return_value=session)
    session.__aexit__ = mock.AsyncMock(return_value=None)

    subscription = Subscription()
    with pytest.raises(APIError) as e:
        await subscription.request(session)
    assert e.type is APIError
    expected_message = "An unknown error occurred."
    assert expected_message == str(e.value)


def test_old_names_warn_and_point_at_the_caller():
    resp = SubscriptionResp.model_validate(
        {
            "tier": 3,
            "active": True,
            "expiresAt": 1708646400,
            "perks": {
                "maxPriorityActions": 1000,
                "startPriority": 10,
                "moduleTrainingSteps": 10000,
                "unlimitedMaxPriority": False,
                "contextTokens": 8192,
            },
            "trainingStepsLeft": {"fixedTrainingStepsLeft": 0, "purchasedTrainingSteps": 0},
            "accountType": 0,
        }
    )
    with pytest.warns(DeprecationWarning, match="use tier_name") as record:
        assert resp.get_tier_name == "Opus"
    assert record[0].filename == __file__
    with pytest.warns(DeprecationWarning, match="use disabled_perks") as record:
        assert resp.limit_perks == resp.disabled_perks == ["unlimitedMaxPriority"]
    assert record[0].filename == __file__
