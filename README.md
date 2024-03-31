![banner](https://github.com/LlmKira/novelai-python/blob/dev/playground/banner-raw.png?raw=true)

---

[![PyPI version](https://badge.fury.io/py/novelai-python.svg)](https://badge.fury.io/py/novelai-python)
[![Downloads](https://pepy.tech/badge/novelai_python)](https://pepy.tech/project/novelai_python)

✨ NovelAI api python sdk with Pydantic.

The goal of this repository is to use Pydantic to build legitimate requests to access the NovelAI API service.

### Roadmap 🚧

- [x] tool.random_prompt
- [x] tool.paint_mask
- [x] tool.image_metadata
- [x] /ai/generate-image
- [x] /user/subscription
- [x] /user/login
- [x] /user/information
- [x] /ai/upscale
- [x] /ai/generate-image/suggest-tags
- [x] /ai/generate-voice
- [ ] /ai/annotate-image
- [ ] /ai/classify
- [ ] /ai/generate-prompt
- [ ] /ai/generate

> GenerateImageInfer.calculate_cost is correct in most cases, but please request account information to get accurate
> consumption information.

> This repo is maintained by me personally now. If you have any questions, please feel free to open an issue.

### Usage 🖥️

```shell
pip install novelai-python
```

More examples can be found in the [playground](https://github.com/LlmKira/novelai-python/tree/main/playground)
directory, read code as documentation.

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
from novelai_python.tool.random_prompt import RandomPromptGenerator

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


