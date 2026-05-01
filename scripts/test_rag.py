from app.rag import generate_rag_response

preguntas = [
    "¿Qué es Python?",
    "¿Qué es Django?",
    "¿Para qué sirve una migración en Django?",
    "¿Qué es una API REST?",
    "¿Qué significa HTTP 404?",
    "¿Qué es un JOIN en SQL?"
]

for pregunta in preguntas:
    print("=" * 80)
    print("PREGUNTA:", pregunta)
    respuesta = generate_rag_response(
        user_text=pregunta,
        intent_name="BuscarEnDocumentacion",
        parameters={}
    )
    print("RESPUESTA:", respuesta)
