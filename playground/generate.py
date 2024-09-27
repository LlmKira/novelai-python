import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError, LoginCredential
from novelai_python import JwtCredential
from novelai_python.sdk.ai.generate import TextLLMModel, LLM, AdvanceLLMSetting
from novelai_python.sdk.ai.generate._enum import get_model_preset

load_dotenv()
jwt = os.getenv("NOVELAI_JWT", None)
if jwt is None:
    raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
credential = JwtCredential(jwt_token=SecretStr(jwt))


async def chat(prompt="Hello"):
    """Or you can use the login credential to get the renewable jwt token"""
    _login_credential = LoginCredential(
        username=os.getenv("NOVELAI_USER"),
        password=SecretStr(os.getenv("NOVELAI_PASS"))
    )
    # await _login_credential.request()
    # print(f"Model List:{enum_to_list(TextLLMModel)}")
    try:
        agent = LLM.build(
            prompt=prompt,
            model=TextLLMModel.ERATO,
            parameters=get_model_preset(TextLLMModel.ERATO).get_all_presets()[0].parameters,
            advanced_setting=AdvanceLLMSetting(
                min_length=1,
                max_length=None,  # Auto
            )
        )
        # NOTE:parameter > advanced_setting, which logic in generate/__init__.py
        # If you not pass the parameter, it will use the default preset.
        # So if you want to set the generation params, you should pass your own params.
        # Only if you want to use some params not affect the generation, you can use advanced_setting.
        result = await agent.request(session=_login_credential)
    except APIError as e:
        logger.exception(e)
        print(f"Error: {e.message}")
        return None
    except Exception as e:
        logger.exception(e)
    else:
        print(f"Result:\n{result.text}")


loop = asyncio.new_event_loop()
loop.run_until_complete(chat(
    prompt="a fox jumped over the lazy dog, and the dog barked at the fox. The fox ran away."
))
