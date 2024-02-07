# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午10:16
# @Author  : sudoskys
# @File    : subscription.py
# @Software: PyCharm
import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError, SubscriptionResp
from novelai_python import Subscription, JwtCredential

load_dotenv()

enhance = "year 2023,dynamic angle, best quality, amazing quality, very aesthetic, absurdres"
token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(jwt))
    try:
        _res = await Subscription().request(
            session=globe_s
        )
    except APIError as e:
        logger.exception(e)
        print(e.response)
        return

    _res: SubscriptionResp
    print(_res)
    print(_res.is_active)
    print(_res.anlas_left)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
