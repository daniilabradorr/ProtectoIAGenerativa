from app.rag import generate_rag_response


def handle_dialogflow_webhook(body: dict) -> dict:
    """
    Proceso la peticion enviada a Dialogflolw.
    Extraigo el intent, texto del usuario y parámetros.
    Devuelvo una respuesta compatible con Dialogflow.
    """

    query_result = body.get("queryResult", {})

    intent_data = query_result.get("intent", {})
    intent_name = intent_data.get("displayName", "")

    user_text = query_result.get("queryText", "")
    parameters = query_result.get("parameters", {})

    print("Intent detectado:", intent_name)
    print("Texto del usuario:", user_text)
    print("Parámetros:", parameters)

    static_responses = {
        "Saludo": "Hola, soy tu asistente técnico por voz. ¿Qué necesitas consultar?",
        "Despedida": "Perfecto, encantado de ayudarte. Hasta luego.",
        "AyudaGeneral": "Puedo ayudarte con dudas de programación, errores, comandos y documentación técnica.",
        "CancelarConsulta": "De acuerdo, cancelo la consulta actual. Puedes hacerme otra pregunta.",
        "CambiarTema": "Perfecto, cambiamos de tema. Dime qué nueva consulta quieres hacer.",
        "ConfirmarConsulta": "Perfecto, continúo con la consulta."
    }

    if intent_name in static_responses:
        answer = static_responses[intent_name]

    elif intent_name in [
        "ExplicarConcepto",
        "BuscarEnDocumentacion",
        "ResolverError",
        "PedirEjemploCodigo",
        "ConsultarComando",
        "VolverConsultaAnterior"
    ]:
        answer = generate_rag_response(
            user_text=user_text,
            intent_name=intent_name,
            parameters=parameters
        )

    else:
        answer = "No he podido identificar correctamente la intención. ¿Puedes reformular la pregunta?"

    return {
        "fulfillmentText": answer
    }