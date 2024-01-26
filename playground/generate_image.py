# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 下午12:23
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import asyncio
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError
from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential

load_dotenv()

enhance = "year 2023,dynamic angle, best quality, amazing quality, very aesthetic, absurdres"
token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(jwt))
    try:
        _res = await GenerateImageInfer.build(
            prompt=f"1girl, winter, jacket, sfw, angel, flower,{enhance}").generate(
            session=globe_s)
    except APIError as e:
        print(e.response)
        return

    _res: ImageGenerateResp
    print(_res.meta)
    file = _res.files[0]
    with open("generate_image.png", "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
