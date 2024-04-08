import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from novelai_python import APIError, Login
from novelai_python import JwtCredential
from novelai_python.sdk.ai.generate_stream import TextLLMModel, LLMStream, LLMStreamResp

load_dotenv()
jwt = os.getenv("NOVELAI_JWT", None)
if jwt is None:
    raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")
credential = JwtCredential(jwt_token=SecretStr(jwt))


async def stream(prompt="Hello"):
    """Or you can use the login credential to get the renewable jwt token"""
    _login_credential = Login.build(
        user_name=os.getenv("NOVELAI_USER"),
        password=os.getenv("NOVELAI_PASS")
    )
    # await _login_credential.request()
    # print(f"Model List:{enum_to_list(TextLLMModel)}")
    try:
        agent = LLMStream.build(
            prompt=prompt,
            model=TextLLMModel.Kayra,
        )
        _data = []
        # 现在，你可以使用异步for循环来处理每一部分数据
        generator = agent.request(session=credential)
        async for data in generator:
            data: LLMStreamResp
            print(data)  # 或者做其他需要的处理
            _data.append(data)
        print(LLMStreamResp.dispatch_stream(_data, model=TextLLMModel.Kayra))
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    except Exception as e:
        logger.exception(e)
    else:
        print(f"Meta: {_data}")


loop = asyncio.get_event_loop()
loop.run_until_complete(stream())
