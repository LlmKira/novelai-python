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
the [NovelAI API service](https://image.novelai.net/docs).

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
- Optional metrics (`pip install "novelai-python[metrics]"`): every request counted and timed, Anlas and the
  Opus usage bar as gauges, `GET /metrics` on the bundled server. `RequestPacer` keeps a random gap between
  requests counted from the end of the previous one; retries after HTTP 500 back off with jitter.

### ⬆️ Upgrading from 0.7

Some changes do not raise an error, so check these when you upgrade:

- **`HTTP(S)_PROXY` is ignored.** Sessions use `trust_env=False`, so a system proxy no longer routes NovelAI
  traffic by accident. Pass `proxy="http://user:pass@host:port"` to the credential (`ApiCredential`,
  `LoginCredential`, ...) or to `Login`; tokenizer downloads and tag suggestions read `NOVELAI_PROXY`.
- **The default model is V5** (`nai-diffusion-5-full`) in `GenerateImageInfer` and `build_generate`.
- **Images come back as PNG** by default (`image_format`), with the metadata in text chunks; set `parameters.image_format = ImageFormat.WEBP` for smaller files.
- **`auto_text`** (V5 only, on by default): quoted text in the prompt is appended as a `, teXt: ...` block, as
  novelai.net does. Pass `auto_text=False` to send the prompt untouched.
- **Image and user endpoints moved to `image.novelai.net`**; `api.novelai.net` rejects third-party clients
  there.
- **Browser identity**: requests carry the headers of Chrome 155 on Windows, as the web client sends them.
  Accept-Language is English (`en-US,en;q=0.9`) unless the credential says otherwise:
  `ApiCredential(..., accept_language="en-sg")` (see `ACCEPT_LANGUAGES`) or a full header value.
- **The image budget is off by default.** Pass `limiter=True` to `request()` / `request_stream()` for the
  process-wide budget (`NOVELAI_DAILY_IMAGE_LIMIT`, default 2500 per 24h, saved to
  `~/.novelai_python/image_limit.json`), or a `DailyImageLimiter` of your own. The budget is shared by all
  tokens and by every limiter, in any process, that uses the same state file.
- **Server: `POST /ai/augment-image` takes the image as the request body** (`application/octet-stream`); the
  other fields stay query parameters. Send `Authorization: Bearer <token>` or the bare token.

- [New Model. No Restrictions. V4.5 Full Is Here.](https://blog.novelai.net/novelai-diffusion-v4-5-full-release-678318c86205)
- [NovelAI Diffusion V4.5 Curated is Here!](https://blog.novelai.net/novelai-diffusion-v4-5-curated-is-here-9e5ba1f628f3)
- [Image Generation Model Release — NovelAI Anime Diffusion V4 Curated Preview (EN)](https://blog.novelai.net/release-novelai-anime-diffusion-v4-curated-preview-en-ca4b0b11e671)
- [Tutorial: Creating Consistent Characters with NovelAI Diffusion Anime [Female]](https://blog.novelai.net/tutorial-en-creating-consistent-characters-with-novelai-diffusion-anime-female-538b4b678a4e)

### 📦 Usage

```shell
pip install -U novelai-python
```

All API users must adhere to the NovelAI Terms of Service: https://novelai.net/terms.

**More examples can be found in the [playground](https://github.com/LlmKira/novelai-python/tree/main/playground)
directory, read code as documentation.**

```python
import asyncio
import os

from pydantic import SecretStr

from novelai_python import GenerateImageInfer, ImageGenerateResp, ApiCredential
from novelai_python.sdk.ai.generate_image import Model, Character, Sampler, UCPreset
from novelai_python.sdk.ai.generate_image.schema import PositionMap

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
print(sub.anlas_left, sub.tier_name, sub.is_unlimited_image_generation)

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

#### 📈 Metrics (Prometheus / VictoriaMetrics)

```shell
pip install "novelai-python[metrics]"
```

Every request the SDK sends is counted and timed; `/user/subscription` and `/user/data` responses also refresh
per-account gauges (Anlas, tier, the Opus usage bar). Nothing is collected without the extra, and
`NOVELAI_METRICS=0` turns it off with the extra installed.

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `novelai_requests_total` | counter | `endpoint`, `model`, `status` | requests by endpoint path, model and outcome: the HTTP status, `transport` (no answer: SSL, DNS, timeout) or `stream_error` |
| `novelai_request_seconds` | histogram | `endpoint`, `model` | wall time of one request, proxy included |
| `novelai_inflight_requests` | gauge | `endpoint` | requests waiting for NovelAI right now |
| `novelai_images_total` | counter | `model` | images received |
| `novelai_stream_frames_total` | counter | `model` | frames of `/ai/generate-image-stream`, previews included |
| `novelai_retries_total` / `novelai_retry_wait_seconds` | counter / histogram | `endpoint` / - | retries after HTTP 500 and the backoff slept before them |
| `novelai_pacing_wait_seconds` | histogram | - | time a request waited for the gap after the previous one (`RequestPacer`) |
| `novelai_last_success_timestamp_seconds` | gauge | `endpoint` | when the endpoint last answered 2xx |
| `novelai_local_limit_remaining_images` | gauge | - | images left in the local `DailyImageLimiter` |
| `novelai_anlas_available` / `_fixed` / `_purchased` | gauge | `account` | Anlas balance |
| `novelai_subscription_tier` / `_active` / `_expires_timestamp_seconds` | gauge | `account` | subscription state |
| `novelai_opus_usage_percent` / `_negative` / `_refill_percent_per_day`, `novelai_opus_images_left` | gauge | `account` | the Opus V5 usage bar |
| `novelai_account_updated_timestamp_seconds` | gauge | `account` | when the account gauges were last refreshed |
| `novelai_sdk_info` | info | `version`, `impersonate` | SDK version and the Chrome profile it impersonates |

Names follow the Prometheus conventions VictoriaMetrics recommends: counters end in `_total`, durations and
timestamps are in seconds, and every label has a small fixed set of values (an endpoint path, a model name, a
status, a short account id). Prompts, seeds, job ids and emails never become label values. The `account` label
is `credential.metrics_label` when set, otherwise the first 8 hex digits of a SHA-256 of the username or token.

Expose the registry for a scrape (pull is the better default), or push from a short-lived script:

```python
from novelai_python import get_metrics

metrics = get_metrics()
metrics.start_http_server(9108)  # http://127.0.0.1:9108/metrics for vmagent / Prometheus
app.mount("/metrics", metrics.asgi_app())  # inside your own FastAPI / Starlette app
metrics.push_to_victoriametrics("http://victoria:8428", extra_labels={"job": "nai", "instance": "worker-1"})
metrics.write_textfile("/var/lib/node_exporter/novelai.prom")  # textfile collector
```

The bundled server (`python -m novelai_python.server`) serves `GET /metrics` too; set `NOVELAI_METRICS_TOKEN`
to require `Authorization: Bearer <token>` on it. Your own registry: `set_metrics(NovelAIMetrics(registry=r))`.

MetricsQL / PromQL that pays off:

```promql
sum(rate(novelai_requests_total{status!~"2.."}[5m])) by (endpoint, status)              # errors per second
histogram_quantile(0.95, sum(rate(novelai_request_seconds_bucket[5m])) by (le, model))  # p95 generation time
novelai_anlas_available < 500                                                           # Anlas running out
novelai_opus_usage_negative == 1                                                        # V5 now costs Anlas
time() - novelai_last_success_timestamp_seconds{endpoint="/ai/generate-image"} > 1800   # nothing worked for 30 min
```

#### ⏱️ Pacing: a gap between requests

NovelAI answers `429 Concurrent generation is locked` when a request follows the previous one too closely, and
back-to-back requests do not look like a person at a keyboard. A `RequestPacer` keeps a random gap between
requests, counted **from the end of the previous request**: the first request goes out at once, a request after
a long pause goes out at once, and only a request that follows another one closely waits for what is left of
the gap. Requests through one pacer run one at a time, like one account generates one image at a time.

```python
from novelai_python import RequestPacer, Subscription

pacer = RequestPacer(min_gap=2, max_gap=8)  # seconds; one pacer per account
await gen.request(session, pacer=pacer)  # waits only if the previous request ended < 2-8 s ago
await gen.request(session, pacer=True)  # the process-wide pacer: NOVELAI_REQUEST_GAP="1,10" (default), "0" = off

async with pacer.slot():  # any other request
    await Subscription().request(session)
```

Pacing is off unless asked for. Retries after HTTP 500 are jittered as well: `random(1..3 s) * 2 ** (retry - 1)`.

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

from pydantic import SecretStr

from novelai_python import APIError, LoginCredential
from novelai_python.sdk.ai.generate import TextLLMModel, LLM, get_default_preset, AdvanceLLMSetting
from novelai_python.sdk.ai.generate._enum import get_model_preset

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

Routes: `/health`, `/limit`, `/user/*`, `/ai/*` (docs at `/docs`) and `GET /metrics` when the `metrics` extra is
installed (`NOVELAI_METRICS_TOKEN` protects it with a bearer token).

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


