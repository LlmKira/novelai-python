# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 下午12:23
# @Author  : sudoskys
# @File    : __init__.py.py

import asyncio
import base64
import os
import pathlib
import random

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, LoginCredential
from novelai_python import GenerateImageInfer, ImageGenerateResp, ApiCredential
from novelai_python.sdk.ai.generate_image import Action, Model, Sampler, Character, UCPreset, Params
from novelai_python.sdk.ai.generate_image.schema import PositionMap
from novelai_python.sdk.ai.generate_image.tokenizer import get_prompt_tokenizer
from novelai_python.tool.random_prompt import RandomPromptGenerator
from novelai_python.utils.useful import enum_to_list


async def generate(
        prompt=None,
):
    jwt_token = os.getenv("NOVELAI_JWT", None)
    if jwt_token is None:
        raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
    jwt_credential = ApiCredential(api_token=SecretStr(jwt_token))

    """Or you can use the login credential to get the renewable jwt token"""
    login_credential = LoginCredential(
        username=os.getenv("NOVELAI_USER"),
        password=SecretStr(os.getenv("NOVELAI_PASS"))
    )

    model = Model.NAI_DIFFUSION_4_5_CURATED

    # await _login_credential.request()
    print(f"Action List:{enum_to_list(Action)}")
    print(
        """
        PositionMap
        .1 .3 .5 .7 .9
        A1 B1 C1 D1 E1
        A2 B2 C2 D2 E2
        A3 B3 C3 D3 E3
        ..............
        A5 B5 C5 D5 E5
        """
    )

    # Randomly generate a scene
    prompt_generator = RandomPromptGenerator()
    scene = prompt_generator.generate_scene_composition()
    if prompt is None:
        prompt = scene.pop(0) + ','.join([
            'muelsyse (arknights)'
        ])
    character = [
        Character(
            prompt=c_prompt,
            uc="red hair",
            center=PositionMap.B2
        ) for c_prompt in scene
    ]

    # Length
    tokenizer = get_prompt_tokenizer(model=model)
    print(
        f"Prompt Length {len(tokenizer.encode(prompt))}"
    )

    # Generate
    try:
        agent = GenerateImageInfer.build_generate(
            prompt=os.getenv("TEST_TAG", prompt),
            width=832,
            height=1216,
            model=model,
            character_prompts=None if os.getenv("TEST_TAG") else character,
            sampler=Sampler.K_EULER_ANCESTRAL,
            ucPreset=UCPreset.TYPE0,
            # Recommended, using preset negative_prompt depends on selected model
            qualityToggle=True,
            decrisp_mode=False,
            variety_boost=False,
            # Checkbox in novelai.net
        ).set_mutual_exclusion(True)
        print(f"charge: {agent.calculate_cost(is_opus=True)} if you are vip3")
        print(f"charge: {agent.calculate_cost(is_opus=False)} if you are not vip3")
        result = await agent.request(
            session=login_credential
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


async def direct_use():
    """
    Don't like use build-in method? you can directly initialize the class.
    that's pydantic!
    :return:
    """
    credential = ApiCredential(api_token=SecretStr("pst-5555"))
    result: ImageGenerateResp = await GenerateImageInfer(
        input="1girl",
        model=Model.NAI_DIFFUSION_4_5_FULL,
        parameters=Params(
            width=832,
            height=1216,
            characterPrompts=[],
            seed=random.randint(0, 4294967295 - 7),
            scale=6,
            qualityToggle=True,
            sampler=Sampler.K_EULER_ANCESTRAL,
            ucPreset=UCPreset.TYPE0,
            steps=23,
            n_samples=1,
        )
    ).request(session=credential)
    print(f"Meta: {result.meta}")
    file = result.files[0]
    with open(f"{pathlib.Path(__file__).stem}.png", "wb") as f:
        f.write(file[1])


load_dotenv()
loop = asyncio.new_event_loop()
loop.run_until_complete(generate())
