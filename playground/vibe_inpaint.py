# -*- coding: utf-8 -*-
import asyncio
import os
import pathlib
from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, Login
from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential
from novelai_python.sdk.ai.generate_image import Action, Sampler, Model
from novelai_python.utils.useful import enum_to_list
from novelai_python.utils.useful import create_mask_from_sketch

with open('static_image.png', 'rb') as f:
    ori_bytes = f.read()
with open('static_image_paint.jpg', 'rb') as f:
    sk_bytes = f.read()
return_bytes = create_mask_from_sketch(original_img_bytes=ori_bytes,
                                       sketch_img_bytes=sk_bytes,
                                       jagged_edges=True,
                                       min_block_size=15
                                       )
with open('static_image_paint_mask.png', 'wb') as f:
    f.write(return_bytes)
    print('Mask exported')


async def generate(
        prompt="1girl, holding gun, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres",
        image_path="static_image.png",  # This is the original image
        reference_style_image_path="static_refer.png",  # This is the reference image
        mask_path="static_image_paint_mask.png",  # This is the mask
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
        if not os.path.exists(reference_style_image_path):
            raise ValueError(f"Image not found: {reference_style_image_path}")
        if not os.path.exists(mask_path):
            raise ValueError(f"Image not found: {mask_path}")
        with open(image_path, "rb") as f:
            image = f.read()
        with open(reference_style_image_path, "rb") as f:
            reference_image = f.read()
        with open(mask_path, "rb") as f:
            mask = f.read()
        agent = GenerateImageInfer.build(
            prompt=prompt,
            action=Action.INFILL,
            model=Model.NAI_DIFFUSION_3_INPAINTING,
            sampler=Sampler.K_DPMPP_SDE,
            image=image,
            mask=mask,
            strength=0.6,

            reference_image=reference_image,
            reference_strength=0.6,
            reference_information_extracted=1,

            add_original_image=True,  # This Not affect the vibe generation
            qualityToggle=True,
        )
        print(f"charge: {agent.calculate_cost(is_opus=True)} if you are vip3")
        print(f"charge: {agent.calculate_cost(is_opus=False)} if you are not vip3")
        result = await agent.request(
            session=credential, remove_sign=True
        )
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        print("Meta in result.meta")
    _res: ImageGenerateResp
    file = result.files[0]
    with open(f"{pathlib.Path(__file__).stem}.png", "wb") as f:
        f.write(file[1])


load_dotenv()
loop = asyncio.get_event_loop()
loop.run_until_complete(generate())
