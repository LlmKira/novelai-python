# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 上午11:58
# @Author  : sudoskys
# @File    : upscale.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
# @Time    : 2024/2/14 下午5:20
# @Author  : sudoskys
# @File    : upscale_demo.py
# @Software: PyCharm
# To run the demo, you need an event loop, for instance by using asyncio
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, Upscale
from novelai_python import UpscaleResp, JwtCredential
from novelai_python.sdk.ai.generate_image import Action
from novelai_python.utils.useful import enum_to_list

load_dotenv()

token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def generate(
        image_path="static_refer.png"
):
    globe_s = JwtCredential(jwt_token=SecretStr(jwt))
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} not found")
    with open(image_path, "rb") as f:
        data = f.read()
    try:
        print(f"Action List:{enum_to_list(Action)}")
        upscale = Upscale(image=data)  # Auto detect image size | base64

        _res = await upscale.request(
            session=globe_s, remove_sign=True
        )
    except APIError as e:
        print(e.response)
        return

    # Meta
    _res: UpscaleResp
    print(_res.meta.endpoint)
    file = _res.files
    with open(f"{Path(__file__).stem}.png", "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(generate())
