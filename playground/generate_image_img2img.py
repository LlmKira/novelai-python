# -*- coding: utf-8 -*-
# @Time    : 2024/2/9 下午10:04
# @Author  : sudoskys
# @File    : generate_image_img2img.py

import asyncio
import base64
import os
import pathlib

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError, LoginCredential
from novelai_python import GenerateImageInfer, ImageGenerateResp, ApiCredential
from novelai_python.sdk.ai.generate_image import Action, Sampler
from novelai_python.utils.useful import enum_to_list


async def generate(
        prompt="1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres",
        image_path="static_image.png"
):
    jwt = os.getenv("NOVELAI_JWT", None)
    if jwt is None:
        raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
    credential = ApiCredential(api_token=SecretStr(jwt))
    """Or you can use the login credential to get the jwt token"""
    _login_credential = LoginCredential(
        username=os.getenv("NOVELAI_USER"),
        password=SecretStr(os.getenv("NOVELAI_PASS"))
    )
    # await _login_credential.request()
    print(f"Action List:{enum_to_list(Action)}")
    print(f"Image Path: {image_path}")
    try:
        if not os.path.exists(image_path):
            raise ValueError(f"Image not found: {image_path}")
        with open(image_path, "rb") as f:
            # Base64 encode the image
            image = base64.b64encode(f.read()).decode()
            # image = f.read() # Or you can use the raw bytes
        agent = GenerateImageInfer.build_img2img(
            prompt=prompt,
            sampler=Sampler.K_DPMPP_SDE,
            image=image,
            seed=123456789,
            extra_noise_seed=123123123,
        )
        print(f"charge: {agent.calculate_cost(is_opus=True)} if you are vip3")
        print(f"charge: {agent.calculate_cost(is_opus=False)} if you are not vip3")
        result = await agent.request(
            session=_login_credential
        )
        logger.info("Using login credential")
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        print(f"Meta: {result.meta}")
    _res: ImageGenerateResp
    file = result.files[0]
    with open(f"{pathlib.Path(__file__).stem}.png", "wb") as f:
        f.write(file[1])
    logger.warning(f"If you use the nai-generated image as input,please diff the seed!")


load_dotenv()
loop = asyncio.new_event_loop()
loop.run_until_complete(generate(image_path="static_refer.png"))
