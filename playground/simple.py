import asyncio


async def main():
    from pydantic import SecretStr
    from novelai_python import GenerateImageInfer, ApiCredential, LoginCredential
    credential = LoginCredential(
        username="NOVELAI_USERNAME",
        password=SecretStr("NOVELAI_PASSWORD")
    )
    gen = GenerateImageInfer.build(
        prompt="1girl, year 2023, dynamic angle, best quality, amazing quality, very aesthetic, absurdres")
    print(f"消耗点数: vip3:{gen.calculate_cost(is_opus=True)}, {gen.calculate_cost(is_opus=False)}")
    resp = await gen.request(session=credential)
    with open("image.png", "wb") as f:
        f.write(resp.files[0][1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
