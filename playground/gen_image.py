# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 下午12:23
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import asyncio
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential

load_dotenv()

enhance = "year 2023,dynamic angle,  best quality, amazing quality, very aesthetic, absurdres"


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(os.getenv("NOVELAI_JWT")))
    _res = await GenerateImageInfer.build(
        prompt=f"1girl,{enhance}").generate(
        session=globe_s)
    _res: ImageGenerateResp
    print(_res.meta)
    file = _res.files[0]
    with open(file[0], "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
