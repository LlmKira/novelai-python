# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 下午12:23
# @Author  : sudoskys
# @File    : __init__.py.py

import asyncio
import os
import pathlib

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, LoginCredential
from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential
from novelai_python.sdk.ai.generate_image import Action, Model, Sampler, Character, UCPreset
from novelai_python.sdk.ai.generate_image.schema import PositionMap
from novelai_python.utils.useful import enum_to_list


async def generate(
        prompt="1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres"
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
    # await _login_credential.request()
    print(f"Action List:{enum_to_list(Action)}")
    print(
        """
        .1 .3 .5 .7 .9
        A1 B1 C1 D1 E1
        A2 B2 C2 D2 E2
        A3 B3 C3 D3 E3
        ..............
        A5 B5 C5 D5 E5
        """
    )
    try:
        agent = GenerateImageInfer.build_generate(
            prompt=prompt,
            model=Model.NAI_DIFFUSION_3,
            character_prompts=[
                Character(
                    prompt="1girl",
                    uc="red hair",
                    center=PositionMap.AUTO
                ),
                Character(
                    prompt="1boy",
                    center=PositionMap.E5
                )
            ],
            sampler=Sampler.K_EULER_ANCESTRAL,
            ucPreset=UCPreset.TYPE0,
            # Recommended, using preset negative_prompt depends on selected model
            qualitySuffix=True,
            qualityToggle=True,
            decrisp_mode=False,
            variety_boost=True,
            # Checkbox in novelai.net
        )
        print(f"charge: {agent.calculate_cost(is_opus=True)} if you are vip3")
        print(f"charge: {agent.calculate_cost(is_opus=False)} if you are not vip3")
        result = await agent.request(
            session=_login_credential
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
loop.run_until_complete(generate())
