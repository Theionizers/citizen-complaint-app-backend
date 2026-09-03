from openai import OpenAI

from app.core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe_audio(audio_file) -> str:
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=audio_file,
    )

    return transcription.text