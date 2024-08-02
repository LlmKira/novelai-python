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
    mock_response.json = AsyncMock(return_value={"statusCode": 200, "message": "Success"})
    session = mock.MagicMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=mock_response)
    session.headers = {}

    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    voice_generate = VoiceGenerate(
        text="Hello, world!",
        voice=-1,
        seed="seed",
        opus=False,
        version="v2"
    )

    # Act
    result = await voice_generate.request(session=session)

    # Assert
    session.get.assert_called_once_with(
        voice_generate.base_url,
        params=voice_generate.model_dump(mode="json", exclude_none=True)
    )
    assert isinstance(result, VoiceResponse)
    assert result.audio == b'audio_content'
