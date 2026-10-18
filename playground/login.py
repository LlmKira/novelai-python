# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:07
# @Author  : sudoskys
# @File    : login.py

import asyncio
import logging
import os

from dotenv import load_dotenv

from novelai_python import APIError, Login, LoginResp

logger = logging.getLogger(__name__)

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
