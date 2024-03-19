# -*- coding: utf-8 -*-
import asyncio
import os
import pathlib
from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, Login
from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential
from novelai_python.sdk.ai.generate_image import Action, Sampler
from novelai_python.utils.useful import enum_to_list


async def generate(
        prompt="1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres",
        image_path="static_refer_banner.png"
):
    jwt = os.getenv("NOVELAI_JWT", None)
    if jwt is None:
        raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
    credential = JwtCredential(jwt_token=SecretStr(jwt))
    """Or you can use the login credential to get the jwt token"""
    _login_credential = Login.build(
        user_name=os.getenv("NOVELAI_USER"),
        password=os.getenv("NOVELAI_PASS")
    )
    # await _login_credential.request()
    print(f"Action List:{enum_to_list(Action)}")
    try:
        if not os.path.exists(image_path):
            raise ValueError(f"Image not found: {image_path}")
        with open(image_path, "rb") as f:
            image = f.read()
        agent = GenerateImageInfer.build(
            prompt=prompt,
            action=Action.GENERATE,
            sampler=Sampler.K_DPMPP_SDE,
            reference_image=image,
            reference_strength=0.9,
            reference_information_extracted=1,
            add_original_image=True,  # This Not affect the vibe generation
            qualityToggle=True,
        )
        print(f"charge: {agent.calculate_cost(is_opus=True)} if you are vip3")
        print(f"charge: {agent.calculate_cost(is_opus=False)} if you are not vip3")
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
loop = asyncio.get_event_loop()
loop.run_until_complete(generate())
