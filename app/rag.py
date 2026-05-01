from typing import Any

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from openai import OpenAI

from app.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    VECTOR_DB_PATH,
)


def get_collection():
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )


def retrieve_context(question: str, n_results: int = 4) -> list[dict[str, Any]]:
    collection = get_collection()

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []

    for doc, meta, distance in zip(documents, metadatas, distances):
        retrieved.append(
            {
                "text": doc,
                "source": meta.get("source", "desconocido"),
                "chunk": meta.get("chunk", ""),
                "distance": distance,
            }
        )

    return retrieved


def build_context(results: list[dict[str, Any]]) -> str:
    context_parts = []

    for item in results:
        context_parts.append(
            f"Fuente: {item['source']} | Chunk: {item['chunk']}\n"
            f"{item['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


def has_relevant_context(results: list[dict[str, Any]]) -> bool:
    if not results:
        return False

    best_distance = results[0]["distance"]

    print("Mejor distancia encontrada:", best_distance)

    return best_distance <= 0.85


def generate_answer_without_llm(question: str, context: str, sources: list[str]) -> str:
    """
    Respuesta de respaldo si no hay API key.
    Sirve para comprobar que el RAG recupera información real desde ChromaDB.
    """
    return (
        "He encontrado información relacionada en la base de conocimiento.\n\n"
        f"Pregunta: {question}\n\n"
        f"Contexto recuperado:\n{context[:1200]}\n\n"
        f"Fuentes consultadas: {', '.join(sources)}"
    )


def generate_answer_with_llm(
    question: str,
    context: str,
    intent_name: str,
    parameters: dict,
) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = """
Eres un asistente técnico de programación.
Responde siempre en español.
Usa únicamente la información del contexto proporcionado.
No inventes información.
Si el contexto no contiene la respuesta, di que no tienes información suficiente.
Responde de forma clara, breve y útil.
"""

    user_prompt = f"""
Intención detectada por Dialogflow: {intent_name}
Parámetros extraídos: {parameters}

Pregunta del usuario:
{question}

Contexto recuperado:
{context}

Genera una respuesta natural para el usuario.
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    return response.output_text


def generate_rag_response(
    user_text: str,
    intent_name: str,
    parameters: dict,
) -> str:
    try:
        results = retrieve_context(user_text)
    except Exception as error:
        return (
            "No he podido consultar la base de conocimiento. "
            f"Detalle técnico: {str(error)}"
        )

    if not has_relevant_context(results):
        return (
            "No he encontrado información suficiente en la base de conocimiento "
            "para responder con seguridad."
        )

    context = build_context(results)
    sources = sorted({item["source"] for item in results})

    if not OPENAI_API_KEY:
        return generate_answer_without_llm(
            question=user_text,
            context=context,
            sources=sources,
        )

    try:
        answer = generate_answer_with_llm(
            question=user_text,
            context=context,
            intent_name=intent_name,
            parameters=parameters,
        )
    except Exception as error:
        return (
            "He recuperado información de la base de conocimiento, "
            "pero ha fallado la generación con el LLM.\n\n"
            f"Detalle técnico: {str(error)}\n\n"
            f"Contexto recuperado:\n{context[:1200]}"
        )

    return f"{answer}\n\nFuentes consultadas: {', '.join(sources)}"