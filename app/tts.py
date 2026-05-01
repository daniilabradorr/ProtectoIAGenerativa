from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_TTS_MODEL, OPENAI_TTS_VOICE


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def synthesize_speech(text: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Falta OPENAI_API_KEY en el archivo .env")

    client = OpenAI(api_key=OPENAI_API_KEY)

    output_path = OUTPUT_DIR / f"respuesta_{uuid4().hex}.mp3"

    with client.audio.speech.with_streaming_response.create(
        model=OPENAI_TTS_MODEL,
        voice=OPENAI_TTS_VOICE,
        input=text[:4000],
    ) as response:
        response.stream_to_file(output_path)

    return str(output_path)