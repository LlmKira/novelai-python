import asyncio
import base64
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, Login
from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential
from novelai_python.sdk.ai.generate_image import Action

load_dotenv()

enhance = "year 2023,dynamic angle, best quality, amazing quality, very aesthetic, absurdres"
token = None
jwt = os.getenv("NOVELAI_JWT") or token


async def main():
    jwt_class = JwtCredential(jwt_token=SecretStr(jwt))
    _res = await Login.build(user_name=os.getenv("NOVELAI_USER"), password=os.getenv("NOVELAI_PASS")
                             ).request()
    with open("raw_test_image.png", "rb") as f:
        data = f.read()
    # Base64 encode the data
    encoded = base64.b64encode(data).decode()
    try:
        gen = GenerateImageInfer.build(
            prompt=f"1girl, spring, jacket, sfw, angel, flower,{enhance}",
            action=Action.GENERATE,
            image=encoded,
            add_original_image=True,
            strength=0.6,
            reference_mode=True,  # IMPORTANT
            width=1088,
            height=896
        )
        cost = gen.calculate_cost(is_opus=True)
        print(f"charge: {cost} if you are vip3")
        print(f"charge: {gen.calculate_cost(is_opus=True)}")
        _res = await gen.request(
            session=jwt_class, remove_sign=True
        )
    except APIError as e:
        print(e.response)
        return

    _res: ImageGenerateResp
    print(_res.meta)
    file = _res.files[0]
    with open("generate_image_transfer.png", "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
