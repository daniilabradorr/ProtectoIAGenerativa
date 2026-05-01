import uuid

from google.cloud import dialogflow_v2 as dialogflow

from app.config import DIALOGFLOW_LANGUAGE_CODE, DIALOGFLOW_PROJECT_ID


def detect_intent_text(text: str, session_id: str | None = None) -> dict:
    if not DIALOGFLOW_PROJECT_ID:
        raise ValueError("Falta DIALOGFLOW_PROJECT_ID en el archivo .env")

    session_client = dialogflow.SessionsClient()

    if session_id is None:
        session_id = str(uuid.uuid4())

    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)

    text_input = dialogflow.TextInput(
        text=text,
        language_code=DIALOGFLOW_LANGUAGE_CODE,
    )

    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={
            "session": session,
            "query_input": query_input,
        }
    )

    query_result = response.query_result

    return {
        "query_text": query_result.query_text,
        "intent_name": query_result.intent.display_name,
        "confidence": query_result.intent_detection_confidence,
        "fulfillment_text": query_result.fulfillment_text,
    }