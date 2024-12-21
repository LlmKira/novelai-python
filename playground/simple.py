import asyncio

from novelai_python.sdk.ai.generate_image import Model


async def main():
    from pydantic import SecretStr
    from novelai_python import GenerateImageInfer, LoginCredential
    credential = LoginCredential(
        username="NOVELAI_USERNAME",
        password=SecretStr("NOVELAI_PASSWORD")
    )
    gen = GenerateImageInfer.build_generate(
        prompt="1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres",
        model=Model.NAI_DIFFUSION_3,
    )
    print(f"消耗点数: vip3:{gen.calculate_cost(is_opus=True)}, {gen.calculate_cost(is_opus=False)}")
    resp = await gen.request(session=credential)
    with open("image.png", "wb") as f:
        f.write(resp.files[0][1])


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
