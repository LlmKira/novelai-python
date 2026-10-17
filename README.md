![banner](https://github.com/LlmKira/novelai-python/blob/dev/playground/banner-raw.png?raw=true)

---

[![PyPI version](https://badge.fury.io/py/novelai-python.svg)](https://badge.fury.io/py/novelai-python)
[![Downloads](https://pepy.tech/badge/novelai_python)](https://pepy.tech/project/novelai_python)


>**Declaration** (2025/06/04)
>
>**I have nothing to do with NovelAI.**
>
>Due to various considerations, such as NovelAI's confusing project architecture and "can't learn anything from it", this project will be in a *non-active* maintenance state. If you have any questions, please *raise an issue*.
>
>This project is designed to be a sample project for me to write Python SDK. It turns out that Pydantic is very powerful.
>
>*I will invest more time in open source projects that are more beneficial to society.*
>

✨ NovelAI api python sdk with Pydantic, modern and user-friendly.

The goal of this repository is to use Pydantic to build legitimate requests to access
the [NovelAI API service](https://api.novelai.net/docs).

> Python >= 3.12 is required (tested on 3.12 – 3.14).

### 📰 News

- **NovelAI Diffusion V5** family: `nai-diffusion-5-full`, `-full-medium` (fast, 14 steps), `-curated` and their
  `-inpainting` variants, with the web client's quality presets (`standard` / `light` / `none`) and negative
  presets. Every model uses `params_version` 4 (`ucPresetId` / `qualityPresetId`) and the
  `multipart/form-data` body the web client sends.
- **Streaming**: `async for event in gen.request_stream(session)` on `/ai/generate-image-stream` yields
  intermediate previews and the final image per sample.
- New: character reference (V4.5), `EncodeVibe`, transparent background (V5), `Upscale` on the image host,
  `UserData`, `TrialStatus`, `Priority`, `CreatePersistentToken`, the OpenAI-compatible text API (`/oa/v1`),
  and `GenerateImageInfer.from_metadata()` to rebuild a request from an image's metadata.
- Fewer dependencies: pydantic, curl_cffi, msgpack, Pillow, numpy, pynacl and tokenizers. httpx, opencv,
  argon2-cffi, ftfy/regex and `bchlib` are gone (`bchlib` has no Python 3.14 wheel; a NumPy BCH codec
  replaces it).
- Optional local image budget (`limiter=True`, see below).

### ⬆️ Upgrading from 0.7

Some changes do not raise an error, so check these when you upgrade:

- **`HTTP(S)_PROXY` is ignored.** Sessions use `trust_env=False`, so a system proxy no longer routes NovelAI
  traffic by accident. Pass `proxy="http://user:pass@host:port"` to the credential (`ApiCredential`,
  `LoginCredential`, ...) or to `Login`; tokenizer downloads and tag suggestions read `NOVELAI_PROXY`.
- **The default model is V5** (`nai-diffusion-5-full`) in `GenerateImageInfer` and `build_generate`.
- **V5 returns webp** by default (`image_format`); set `parameters.image_format = ImageFormat.PNG` for PNG.
- **`auto_text`** (V5 only, on by default): quoted text in the prompt is appended as a `, teXt: ...` block, as
  novelai.net does. Pass `auto_text=False` to send the prompt untouched.
- **Image and user endpoints moved to `image.novelai.net`**; `api.novelai.net` rejects third-party clients
  there.
- **The browser identity follows curl_cffi**: User-Agent, `sec-ch-ua` and platform are those of the
  impersonated Chrome, and Accept-Language is `en-US,en;q=0.9`.
- **The image budget is off by default.** Pass `limiter=True` to `request()` / `request_stream()` for the
  process-wide budget (`NOVELAI_DAILY_IMAGE_LIMIT`, default 2500 per 24h, saved to
  `~/.novelai_python/image_limit.json`), or a `DailyImageLimiter` of your own. The budget is per process and
  shared by all tokens it uses.

- [New Model. No Restrictions. V4.5 Full Is Here.](https://blog.novelai.net/novelai-diffusion-v4-5-full-release-678318c86205)
- [NovelAI Diffusion V4.5 Curated is Here!](https://blog.novelai.net/novelai-diffusion-v4-5-curated-is-here-9e5ba1f628f3)
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

prompt = "2girls, fisheye, closeup, from above"


async def main():
    gen = GenerateImageInfer.build_generate(
        prompt=prompt,
        model=Model.NAI_DIFFUSION_5_FULL,  # or NAI_DIFFUSION_4_5_FULL
        character_prompts=[
            Character(
                prompt="1girl, head tilt, short hair, black hair, grey eyes, small breasts, looking at viewer",
                uc="red hair",
                center=PositionMap.B2
            ),
            Character(
                prompt="1girl, fox ears, fox tail, white hair, white tail, white ears",
                uc="black hair",
                center=PositionMap.D2
            )
        ],
        sampler=Sampler.K_EULER_ANCESTRAL,
        ucPreset=UCPreset.TYPE0,
        # Recommended, using preset negative_prompt depends on selected model
        qualityToggle=True,
        decrisp_mode=False,
        variety_boost=True,
        furry_mode=False,
        # Checkbox in novelai.net
    )
    cost = gen.calculate_cost(is_opus=True)
    print(f"charge: {cost} if you are vip3")
    resp = await gen.request(session=session)  # raises DailyLimitExceeded once the local budget is spent
    resp: ImageGenerateResp
    print(resp.meta)
    print(resp.save("./output"))  # auto-download every returned image

    # streaming previews (V5 family)
    async for event in gen.request_stream(session=session):
        if event.is_final:
            open(f"./output/sample_{event.samp_ix}.webp", "wb").write(event.image)
        elif event.event_type == "intermediate":
            print("preview", event.samp_ix, "step", event.step_ix, len(event.image), "bytes")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

```

#### 🔋 Anlas / limit monitoring

```python
from novelai_python import Subscription, UserData, TrialStatus, get_default_limiter

sub = await Subscription().request(session=session)
print(sub.anlas_left, sub.get_tier_name, sub.is_unlimited_image_generation)

data = await UserData().request(session=session)  # subscription + information in one call
print(data.anlas_left)

trial = await TrialStatus().request(session=session)
print(trial.trialImagesLeft)

# only when requests opt in with limiter=True
print(get_default_limiter().status())  # {'limit': 2500, 'used': ..., 'remaining': ..., 'reset_at': ...}
```

`sub.usage` is the Opus V5 usage bar: `percent`, `purchasedPercent` (bought extra, 0-300),
`isNegative`, `timeUntilNextPercent`. `Priority().request(session)` returns the task priority balance;
`CreatePersistentToken(overwrite=True).request(jwt_session)` creates a `pst-...` API key.

#### 🖼️ Transparent background, character reference, vibes

```python
from novelai_python import CharacterReference, EncodeVibe, GenerateImageInfer
from novelai_python.sdk.ai._enum import Model

# V5: "Transparent BG" of the web client (tag before the quality suffix + straight alpha)
gen = GenerateImageInfer.build_generate("1girl, standing", transparent_background=True)

# V4.5: Precise Reference (character / style / costume / character&style / delta)
gen = GenerateImageInfer.build_generate(
    "1girl", model=Model.NAI_DIFFUSION_4_5_FULL,
    character_references=[CharacterReference(image=open("ref.png", "rb").read(), fidelity=0.8)],
)

# V4 / V4.5 vibe transfer takes encoded vibes: encode once, reuse the result
vibe = await EncodeVibe(image=open("vibe.png", "rb").read(), information_extracted=0.7).request(session)
gen = GenerateImageInfer.build_generate(
    "1girl", model=Model.NAI_DIFFUSION_4_5_FULL,
    reference_image_multiple=[vibe.vibe_b64], reference_strength_multiple=[0.6],
    reference_information_extracted_multiple=[0.7],
)
```

V5 has no vibe transfer and no character reference; it takes up to 32 characters (V4/V4.5: 6).

Environment:

| variable | default | meaning |
|---|---|---|
| `NOVELAI_DAILY_IMAGE_LIMIT` | `2500` | images per 24h window, `0` disables |
| `NOVELAI_LIMIT_STATE_FILE` | `~/.novelai_python/image_limit.json` | where the counter is persisted |

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

OpenAI-compatible text API (`text.novelai.net/oa/v1`), responses in OpenAI format:

```python
from novelai_python import OAIChatCompletion, OAIChatMessage, OAIModels

models = await OAIModels().request(session)
req = OAIChatCompletion(model=models.data[0].id, messages=[OAIChatMessage(role="user", content="Hello")])
print((await req.request(session))["choices"][0]["message"]["content"])
async for chunk in req.stream(session):
    print(chunk["choices"][0]["delta"].get("content", ""), end="")
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
pip install "novelai-python[server]"
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


