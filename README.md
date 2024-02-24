# novelai-python

[![PyPI version](https://badge.fury.io/py/novelai-python.svg)](https://badge.fury.io/py/novelai-python)
[![Downloads](https://pepy.tech/badge/novelai_python)](https://pepy.tech/project/novelai_python)

The goal of this repository is to use Pydantic to build legitimate requests to access the Novelai API service.

### Roadmap 🚧

- [x] utils.NovelAiMetadata
- [x] utils.random_prompt
- [x] /ai/generate-image
- [x] /user/subscription
- [x] /user/login
- [x] /user/information
- [x] /ai/upscale
- [x] /ai/generate-image/suggest-tags
- [ ] /ai/annotate-image
- [ ] /ai/classify
- [ ] /ai/generate-prompt
- [ ] /ai/generate
- [ ] /ai/generate-voice

### Usage 🖥️

```shell
pip install novelai-python
```

More examples can be found in the [playground](https://github.com/LlmKira/novelai-python/tree/main/playground) directory.

```python
import asyncio
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential, LoginCredential, ApiCredential

load_dotenv()

enhance = "year 2023,dynamic angle,  best quality, amazing quality, very aesthetic, absurdres"


async def main():
    globe_s = JwtCredential(
        jwt_token=SecretStr(os.getenv("NOVELAI_JWT"))  # ey****
    )
    globe_s1 = ApiCredential(
        api_token=SecretStr(os.getenv("NOVELAI_JWT"))  # pst-***
    )
    globe_s2 = LoginCredential(
        username=os.getenv("NOVELAI_USERNAME"),
        password=SecretStr(os.getenv("NOVELAI_PASSWORD"))
    )

    gen = await GenerateImageInfer.build(
        prompt=f"1girl,{enhance}")
    cost = gen.calculate_cost(is_opus=True)
    print(f"charge: {cost} if you are vip3")

    resp = gen.request(session=globe_s)
    resp: ImageGenerateResp
    print(resp.meta)

    file = resp.files[0]
    with open(file[0], "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

```

#### Random Prompt

```python
from novelai_python.utils.random_prompt import RandomPromptGenerator

s = RandomPromptGenerator(nsfw_enabled=False).random_prompt()
print(s)
```

#### Run A Server

```shell
pip install novelai_python
python3 -m novelai_python.server -h '0.0.0.0' -p 7888
```

## Acknowledgements 🙏

[BackEnd](https://api.novelai.net/docs)

[novelai-api](https://github.com/Aedial/novelai-api)

[NovelAI-API](https://github.com/HanaokaYuzu/NovelAI-API)


