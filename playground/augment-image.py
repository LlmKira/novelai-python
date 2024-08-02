# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 下午12:23
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import asyncio
import os
import pathlib

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, LoginCredential, JwtCredential, ImageGenerateResp
from novelai_python import AugmentImageInfer
from novelai_python.sdk.ai.augment_image import ReqType, Moods


async def generate(
        image,
        request_type: ReqType = ReqType.SKETCH,
):
    jwt = os.getenv("NOVELAI_JWT", None)
    if jwt is None:
        raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
    credential = JwtCredential(jwt_token=SecretStr(jwt))
    """Or you can use the login credential to get the renewable jwt token"""
    _login_credential = LoginCredential(
        username=os.getenv("NOVELAI_USER"),
        password=SecretStr(os.getenv("NOVELAI_PASS"))
    )
    try:
        agent = AugmentImageInfer.build(
            req_type=request_type,
            image=image,
            mood=Moods.Shy,
            prompt="",
            defry=0,
        )
        # print(f"charge: {agent.calculate_cost(is_opus=True)} if you are vip3")
        # print(f"charge: {agent.calculate_cost(is_opus=False)} if you are not vip3")
        result = await agent.request(
            session=credential
        )
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        print(f"Meta: {result.meta}")
    _res: ImageGenerateResp
    file = result.files[0]
    with open(f"{pathlib.Path(__file__).stem}.png", "wb") as f:
        f.write(file[1])


load_dotenv()
loop = asyncio.new_event_loop()
loop.run_until_complete(
    generate(
        image=pathlib.Path(__file__).parent / "static_image.png",
        request_type=ReqType.SKETCH
    )
)
