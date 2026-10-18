# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午8:25
# @Author  : sudoskys
# @File    : suggest_tag.py

import asyncio
import logging
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, JwtCredential, SuggestTags, SuggestTagsResp

logger = logging.getLogger(__name__)

load_dotenv()

token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(jwt))
    try:
        _res = await SuggestTags().request(
            session=globe_s
        )
        _res: SuggestTagsResp
        print(f"Information: {_res}")
        print(_res.model_dump())
    except APIError as e:
        logger.exception(e)
        print(e.__dict__)
        return


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
