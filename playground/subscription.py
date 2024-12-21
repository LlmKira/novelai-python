# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午10:16
# @Author  : sudoskys
# @File    : subscription.py

import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError, SubscriptionResp, LoginCredential
from novelai_python import Subscription, JwtCredential

load_dotenv()

enhance = "year 2023,dynamic angle, best quality, amazing quality, very aesthetic, absurdres"
token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(jwt))
    try:
        sub = Subscription()
        _res = await sub.request(
            session=globe_s
        )
        _res: SubscriptionResp
        print(f"JwtCredential/Subscription: {_res}")
        print(_res.is_active)
        print(_res.anlas_left)
    except APIError as e:
        logger.exception(e)
        print(e.__dict__)
        return

    try:
        cre = LoginCredential(
            username=os.getenv("NOVELAI_USER"),
            password=SecretStr(os.getenv("NOVELAI_PASS"))
        )
        _res = await Subscription().request(
            session=cre
        )
        print(f"LoginCredential/User subscription: {_res}")
        print(_res.is_active)
        print(_res.anlas_left)
    except Exception as e:
        logger.exception(e)


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
