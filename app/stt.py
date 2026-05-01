from pathlib import Path
from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_STT_MODEL


def transcribe_audio(audio_path: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Falta OPENAI_API_KEY en el archivo .env")

    client = OpenAI(api_key=OPENAI_API_KEY)

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=OPENAI_STT_MODEL,
            file=audio_file,
            language="es",
        )

    return transcription.text.strip()