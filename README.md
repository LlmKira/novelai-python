![banner](https://github.com/LlmKira/novelai-python/blob/dev/playground/banner-raw.png?raw=true)

---

[![PyPI version](https://badge.fury.io/py/novelai-python.svg)](https://badge.fury.io/py/novelai-python)
[![Downloads](https://pepy.tech/badge/novelai_python)](https://pepy.tech/project/novelai_python)

✨ NovelAI api python sdk with Pydantic, modern and user-friendly.

The goal of this repository is to use Pydantic to build legitimate requests to access
the [NovelAI API service](https://api.novelai.net/docs).

> Python >= 3.9 is required.

### 📰 News

- [Image Generation Model Release — NovelAI Anime Diffusion V4 Curated Preview (EN)](https://blog.novelai.net/release-novelai-anime-diffusion-v4-curated-preview-en-ca4b0b11e671)
- [Tutorial: Creating Consistent Characters with NovelAI Diffusion Anime [Female]](https://blog.novelai.net/tutorial-en-creating-consistent-characters-with-novelai-diffusion-anime-female-538b4b678a4e)

### 📦 Usage

```shell
pip -U install novelai-python
```

All API users must adhere to the NovelAI Terms of Service: https://novelai.net/terms.

**More examples can be found in the [playground](https://github.com/LlmKira/novelai-python/tree/main/playground)
directory, read code as documentation.**

```python
import asyncio
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import GenerateImageInfer, ImageGenerateResp, ApiCredential
from novelai_python.sdk.ai.generate_image import Model, Character, Sampler, UCPreset
from novelai_python.sdk.ai.generate_image.schema import PositionMap

load_dotenv()
session = ApiCredential(api_token=SecretStr(os.getenv("NOVELAI_JWT")))  # pst-***
# For security reasons, storing user credentials in plaintext is strongly discouraged.

prompt = "1girl, year 2023,dynamic angle,  best quality, amazing quality, very aesthetic, absurdres"


async def main():
    gen = GenerateImageInfer.build_generate(
        prompt=prompt,
        model=Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
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
    cost = gen.calculate_cost(is_opus=True)
    print(f"charge: {cost} if you are vip3")
    resp = await gen.request(session=session)
    resp: ImageGenerateResp
    print(resp.meta)
    file = resp.files[0]
    with open(file[0], "wb") as f:
        f.write(file[1])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

```

#### 📦 LLM

```python
import asyncio
import os

from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import APIError, LoginCredential
from novelai_python.sdk.ai.generate import TextLLMModel, LLM, get_default_preset, AdvanceLLMSetting
from novelai_python.sdk.ai.generate._enum import get_model_preset

load_dotenv()
username = os.getenv("NOVELAI_USER", None)
assert username is not None
# credential = JwtCredential(jwt_token=SecretStr(jwt))
login_credential = LoginCredential(
    username=os.getenv("NOVELAI_USER"),
    password=SecretStr(os.getenv("NOVELAI_PASS"))
)


async def chat(prompt: str):
    try:
        model = TextLLMModel.ERATO  # llama3
        parameters = get_default_preset(model).parameters
        agent = LLM.build(
            prompt=prompt,
            model=model,
            # parameters=None,  # Auto Select or get from preset
            parameters=get_model_preset(TextLLMModel.ERATO).get_all_presets()[0].parameters,  # Select from enum preset
            advanced_setting=AdvanceLLMSetting(
                min_length=1,
                max_length=None,  # Auto
            )
        )
        # NOTE:parameter > advanced_setting, which logic in generate/__init__.py
        # If you not pass the parameter, it will use the default preset.
        # So if you want to set the generation params, you should pass your own params.
        # Only if you want to use some params not affect the generation, you can use advanced_setting.
        result = await agent.request(session=login_credential)
    except APIError as e:
        raise Exception(f"Error: {e.message}")
    print(f"Result: \n{result.text}")


loop = asyncio.get_event_loop()
loop.run_until_complete(chat("Hello"))
```

#### 📦 Random Prompt

```python
from novelai_python.tool.random_prompt import RandomPromptGenerator

generator = RandomPromptGenerator()
for i in range(10):
    print(generator.generate_common_tags(nsfw=False))
    print(generator.generate_scene_tags())
    print(generator.generate_scene_composition())
    print(generator.get_holiday_themed_tags())
```

#### 📦 Run A Server

```shell
pip install novelai_python
python3 -m novelai_python.server -h '127.0.0.1' -p 7888
```

#### 📦 Tokenizer

```python
from novelai_python._enum import get_tokenizer_model, TextLLMModel, TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer

# Through llm model name to get the tokenizer
tokenizer_package = NaiTokenizer(get_tokenizer_model(TextLLMModel.ERATO))
# Directly use the tokenizer
clip_tokenizer = NaiTokenizer(TextTokenizerGroup.CLIP)

# Tokenize a text
t_text = "a fox jumped over the lazy dog"
encode_tokens = tokenizer_package.encode(t_text)
print(tokenizer_package.tokenize_text(t_text))
print(f"Tokenized text: {encode_tokens}")
print(tokenizer_package.decode(tokenizer_package.encode(t_text)))

```

### 🔨 Roadmap

- [x] tool.random_prompt
- [x] tool.paint_mask
- [x] tool.image_metadata
- [x] tokenizer
- [x] /ai/generate-image
- [x] /user/subscription
- [x] /user/login
- [x] /user/information
- [x] /ai/upscale
- [x] /ai/generate-image/suggest-tags
- [x] /ai/generate-voice
- [x] /ai/generate-stream
- [x] /ai/generate
- [x] /ai/augment-image
- [ ] /ai/annotate-image
- [ ] /ai/classify
- [ ] /ai/generate-prompt

> GenerateImageInfer.calculate_cost is correct in most cases, but please request account information to get accurate
> consumption information.

> This repo is maintained by me personally now. If you have any questions, please feel free to open an issue.

## 🚫 About Nsfw

You might need some solutions for identifying NSFW content and adding a mosaic to prevent operational mishaps.

https://dghs-imgutils.deepghs.org/main/api_doc/detect/nudenet.html

https://dghs-imgutils.deepghs.org/main/api_doc/operate/censor.html

## 🙏 Acknowledgements

[novelai-api](https://github.com/Aedial/novelai-api)

[NovelAI-API](https://github.com/HanaokaYuzu/NovelAI-API)


