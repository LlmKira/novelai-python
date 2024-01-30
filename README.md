# novelai-python

[![PyPI version](https://badge.fury.io/py/novelai_python.svg)](https://badge.fury.io/py/novelai_python)
[![Downloads](https://pepy.tech/badge/novelai_python)](https://pepy.tech/project/novelai_python)

The goal of this repository is to use Pydantic to build legitimate requests to access the Novelai API service.

### Roadmap 🚧

- [x] /ai/generate-image
- [ ] /ai/generate-image/suggest-tags
- [ ] /ai/annotate-image
- [ ] /ai/classify
- [ ] /ai/upscale
- [ ] /ai/generate-prompt
- [ ] /ai/generate
- [ ] /ai/generate-voice

### Usage 🖥️

```python
import asyncio
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import GenerateImageInfer, ImageGenerateResp, JwtCredential

load_dotenv()

enhance = "year 2023,dynamic angle,  best quality, amazing quality, very aesthetic, absurdres"


async def main():
    globe_s = JwtCredential(jwt_token=SecretStr(os.getenv("NOVELAI_JWT")))
    _res = await GenerateImageInfer.build(
        prompt=f"1girl,{enhance}").generate(
        session=globe_s)
    _res: ImageGenerateResp
    print(_res.meta)
    file = _res.files[0]
    with open(file[0], "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

```

#### Random Prompt

```python
from novelai_python.utils.random_prompt import RandomPromptGenerator

s = RandomPromptGenerator(nsfw_enabled=False).generate()
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

