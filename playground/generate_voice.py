import asyncio
import os
import pathlib
from dotenv import load_dotenv
from pydantic import SecretStr

from novelai_python import VoiceGenerate, VoiceResponse, JwtCredential, APIError
from novelai_python.sdk.ai.generate_voice import VoiceSpeakerV2, VoiceSpeakerV1
from novelai_python.utils.useful import enum_to_list

load_dotenv()
jwt = os.getenv("NOVELAI_JWT", None)
if jwt is None:
    raise ValueError("NOVELAI_JWT is not set in `.env` file, please create one and set it")


async def generate_voice(text: str):
    credential = JwtCredential(jwt_token=SecretStr(jwt))
    """Or you can use the login credential to get the renewable jwt token"""
    # await _login_credential.request()
    print(f"VoiceSpeakerV2 List:{enum_to_list(VoiceSpeakerV2)}")
    try:
        voice_gen = VoiceGenerate.build(
            text=text,
            voice_engine=VoiceSpeakerV1.Crina,  # VoiceSpeakerV2.Ligeia,
        )
        result = await voice_gen.request(
            session=credential
        )
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        print(f"Meta: {result.meta}")
    _res: VoiceResponse
    # 写出到 同名的 mp3 文件
    file = result.audio
    with open(f"{pathlib.Path(__file__).stem}.mp3", "wb") as f:
        f.write(file)


loop = asyncio.get_event_loop()
loop.run_until_complete(
    generate_voice("Hello, I am a test voice, limit 1000 characters")
)
