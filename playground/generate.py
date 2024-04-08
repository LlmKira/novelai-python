import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError, Login
from novelai_python import JwtCredential
from novelai_python.sdk.ai.generate import TextLLMModel, LLM

load_dotenv()
jwt = os.getenv("NOVELAI_JWT", None)
if jwt is None:
    raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
credential = JwtCredential(jwt_token=SecretStr(jwt))


async def chat(prompt="Hello"):
    """Or you can use the login credential to get the renewable jwt token"""
    _login_credential = Login.build(
        user_name=os.getenv("NOVELAI_USER"),
        password=os.getenv("NOVELAI_PASS")
    )
    # await _login_credential.request()
    # print(f"Model List:{enum_to_list(TextLLMModel)}")
    try:
        agent = LLM.build(
            prompt=prompt,
            model=TextLLMModel.Kayra,
        )
        result = await agent.request(session=credential)
    except APIError as e:
        logger.exception(e)
        print(f"Error: {e.message}")
        return None
    except Exception as e:
        logger.exception(e)
    else:
        print(f"Result: \n{result.text}")


loop = asyncio.get_event_loop()
loop.run_until_complete(chat())
