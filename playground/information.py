# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午4:34
# @Author  : sudoskys
# @File    : information.py
# @Software: PyCharm
import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError
from novelai_python import Information, InformationResp, JwtCredential

load_dotenv()

enhance = "year 2023,dynamic angle, best quality, amazing quality, very aesthetic, absurdres"
token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(jwt))
    try:
        _res = await Information().request(
            session=globe_s
        )
        _res: InformationResp
        print(f"Information: {_res}")
        print(_res.model_dump())
    except APIError as e:
        logger.exception(e)
        print(e.__dict__)
        return


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
