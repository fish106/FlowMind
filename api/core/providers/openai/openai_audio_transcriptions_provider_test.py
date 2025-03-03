import base64
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from core.providers.openai.openai_audio_transcriptions_provider import OpenAIAudioTranscriptionsProvider


@pytest.fixture
def audio_transcriptions_provider() -> OpenAIAudioTranscriptionsProvider:
    return OpenAIAudioTranscriptionsProvider(api_key="test_api_key")


async def test_transcribe_audio(
    audio_transcriptions_provider: OpenAIAudioTranscriptionsProvider,
    httpx_mock: HTTPXMock,
) -> None:
    # Mock audio data
    audio_data = base64.b64encode(b"fake audio data").decode()
    mock_response = {"text": "This is a test transcription."}

    # Mock the httpx response
    httpx_mock.add_response(url="https://api.openai.com/v1/audio/transcriptions", json=mock_response)

    result = await audio_transcriptions_provider.transcribe_audio(audio_data, "wav")

    # Verify the result
    assert result == "This is a test transcription."

    # Verify the API call
    request = httpx_mock.get_request()
    assert request is not None
    assert request.url == "https://api.openai.com/v1/audio/transcriptions"
    assert request.headers["Authorization"] == "Bearer test_api_key"
    assert hasattr(request, "extensions")
    assert request.extensions is not None  # type: ignore
    assert request.extensions["timeout"]["read"] == 300.0  # type: ignore
    assert request.extensions["timeout"]["connect"] == 300.0  # type: ignore
    # Verify the request stream fields
    assert request.stream is not None
    assert hasattr(request.stream, "fields")
    file_fields: Any = request.stream.fields  # type: ignore

    # Check the file fields
    for file in file_fields:
        if file.name == "file":
            assert file.filename == "audio.wav"
            assert file.file is not None
            assert base64.b64encode(file.file.read()).decode() == audio_data
        elif file.name == "model":
            assert file.filename is None
            assert file.file == "whisper-1"
