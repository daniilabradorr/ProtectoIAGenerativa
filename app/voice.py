from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import HTMLResponse

from app.dialogflow_client import detect_intent_text
from app.rag import generate_rag_response
from app.stt import transcribe_audio
from app.tts import synthesize_speech


router = APIRouter()

UPLOAD_DIR = Path("outputs/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/voice", response_class=HTMLResponse)
def voice_page():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Asistente técnico por voz</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 850px;
      margin: 40px auto;
      padding: 20px;
      background: #f7f7f7;
    }
    .card {
      background: white;
      padding: 24px;
      border-radius: 14px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    }
    button {
      padding: 12px 18px;
      margin: 8px 8px 8px 0;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 16px;
    }
    #start { background: #2563eb; color: white; }
    #stop { background: #dc2626; color: white; }
    pre {
      background: #111827;
      color: #e5e7eb;
      padding: 16px;
      border-radius: 10px;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Asistente técnico por voz</h1>
    <p>Pulsa grabar, pregunta algo y después pulsa detener.</p>

    <button id="start">🎙️ Grabar</button>
    <button id="stop" disabled>⏹️ Detener y enviar</button>

    <h3>Resultado</h3>
    <pre id="result">Esperando audio...</pre>

    <h3>Respuesta en voz</h3>
    <audio id="audio" controls></audio>
  </div>

<script>
let mediaRecorder;
let chunks = [];

document.getElementById("start").onclick = async () => {
  chunks = [];
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = event => {
    if (event.data.size > 0) {
      chunks.push(event.data);
    }
  };

  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "pregunta.webm");

    document.getElementById("result").textContent = "Procesando audio...";

    const response = await fetch("/voice/chat", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    document.getElementById("result").textContent =
      "Transcripción: " + data.transcription + "\\n\\n" +
      "Intent: " + data.intent_name + "\\n\\n" +
      "Respuesta: " + data.answer;

    document.getElementById("audio").src = data.audio_url;
    document.getElementById("audio").play();
  };

  mediaRecorder.start();
  document.getElementById("start").disabled = true;
  document.getElementById("stop").disabled = false;
};

document.getElementById("stop").onclick = () => {
  mediaRecorder.stop();
  document.getElementById("start").disabled = false;
  document.getElementById("stop").disabled = true;
};
</script>
</body>
</html>
"""


@router.post("/voice/chat")
async def voice_chat(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    audio_path = UPLOAD_DIR / f"pregunta_{uuid4().hex}{suffix}"

    with open(audio_path, "wb") as buffer:
        buffer.write(await audio.read())

    transcription = transcribe_audio(str(audio_path))

    try:
        dialogflow_result = detect_intent_text(transcription)
        answer = dialogflow_result["fulfillment_text"]
        intent_name = dialogflow_result["intent_name"]

        if not answer:
            answer = generate_rag_response(
                user_text=transcription,
                intent_name=intent_name,
                parameters={},
            )

    except Exception as error:
        intent_name = "FallbackLocalRAG"
        answer = generate_rag_response(
            user_text=transcription,
            intent_name="BuscarEnDocumentacion",
            parameters={},
        )
        answer = (
            f"No he podido consultar Dialogflow directamente: {str(error)}\n\n"
            f"Respuesta local RAG:\n{answer}"
        )

    tts_path = synthesize_speech(answer)
    audio_url = "/" + tts_path.replace("\\", "/")

    return {
        "transcription": transcription,
        "intent_name": intent_name,
        "answer": answer,
        "audio_url": audio_url,
    }