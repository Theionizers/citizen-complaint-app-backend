import os
import tempfile
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def transcribe_audio(uploaded_file):
    """
    Transcribe an uploaded WAV audio file.
    """

    audio_bytes = uploaded_file.read()

    if not audio_bytes:
        raise ValueError("Uploaded audio file is empty.")

    temporary_path = None

    try:
        # Create a real temporary WAV file with a .wav extension
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".wav",
            delete=False
        ) as temp_file:
            temp_file.write(audio_bytes)
            temporary_path = temp_file.name

        # Open the file again so OpenAI receives a filename
        with open(temporary_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        return result.text

    finally:
        if temporary_path and Path(temporary_path).exists():
            Path(temporary_path).unlink()