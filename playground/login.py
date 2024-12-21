# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:07
# @Author  : sudoskys
# @File    : login.py

import asyncio
import os

from dotenv import load_dotenv
from loguru import logger

from novelai_python import APIError
from novelai_python import Login, LoginResp

load_dotenv()


async def main():
    try:
        _res = await Login.build(user_name=os.getenv("NOVELAI_USER"), password=os.getenv("NOVELAI_PASS")
                                 ).request()
    except APIError as e:
        logger.exception(e)
        print(e.__dict__)
        return

    _res: LoginResp
    print(_res)
    print(f"Access Token: {_res.accessToken}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
