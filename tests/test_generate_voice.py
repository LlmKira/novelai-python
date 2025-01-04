from unittest import mock
from unittest.mock import AsyncMock

import pytest
from curl_cffi.requests import AsyncSession

from src.novelai_python.sdk.ai.generate_voice import VoiceGenerate, VoiceResponse


@pytest.mark.asyncio
async def test_request():
    # Arrange
    mock_response = mock.MagicMock()
    mock_response.content = b'audio_content'
    mock_response.headers = {'Content-Type': 'audio/mpeg'}
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"statusCode": 200, "message": "Success"})

    # 使用 AsyncMock 模拟异步方法
    session = mock.MagicMock(spec=AsyncSession)
    session.post = AsyncMock(return_value=mock_response)
    session.headers = {}

    # Mock '__aenter__' 和 '__aexit__'，以兼容异步上下文管理器
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    # 创建 VoiceGenerate 对象
    voice_generate = VoiceGenerate(
        text="Hello, world!",
        voice=-1,
        seed="seed",
        opus=False,
        version="v2"
    )

    # Act
    result = await voice_generate.request(session=session, override_headers=None)

    # Assert
    session.post.assert_called_once_with(
        url=voice_generate.base_url,
        json=voice_generate.model_dump(mode="json", exclude_none=True)
    )
    assert isinstance(result, VoiceResponse)
    assert result.audio == b'audio_content'