from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.voice import router as voice_router
from app.webhook import handle_dialogflow_webhook


app = FastAPI(
    title="Backend IA Conversacional",
    description="Webhook para Dialogflow ES con RAG, STT y TTS",
    version="1.0.0",
)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.include_router(voice_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Backend funcionando correctamente",
        "voice_demo": "http://127.0.0.1:8000/voice",
    }


@app.post("/webhook/dialogflow")
async def dialogflow_webhook(request: Request):
    body = await request.json()
    response = handle_dialogflow_webhook(body)
    return response