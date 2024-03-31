import pytest
from unittest import mock

from curl_cffi.requests import AsyncSession

from src.novelai_python.sdk.ai.generate_voice import VoiceGenerate, VoiceResponse


@pytest.mark.asyncio
async def test_request():
    # Arrange
    mock_response = mock.MagicMock()
    mock_response.content = b'audio_content'
    mock_response.headers = {'Content-Type': 'audio/mpeg'}
    session = mock.MagicMock(spec=AsyncSession)
    session.get = mock.AsyncMock(return_value=mock_response)
    session.headers = {}

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
    session.get.assert_called_once()
    assert isinstance(result, VoiceResponse)
    assert result.audio == b'audio_content'

