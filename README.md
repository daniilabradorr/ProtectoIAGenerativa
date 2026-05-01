# Proyecto IA Conversacional por Voz con Dialogflow ES, OCR, RAG y TTS

## 1. Descripción general

Este proyecto implementa un **asistente técnico conversacional por voz** capaz de resolver dudas de programación utilizando una base de conocimiento propia. El sistema recibe una pregunta hablada, la transcribe mediante un servicio externo de Speech-to-Text, envía el texto a Dialogflow ES para detectar la intención, ejecuta un webhook en FastAPI, consulta documentación técnica mediante RAG y devuelve la respuesta en audio mediante Text-to-Speech externo.

El caso de uso elegido es un **asistente técnico para estudiantes y desarrolladores junior**, orientado a responder preguntas sobre Python, Django, SQL, API REST y conceptos técnicos habituales.

Flujo principal:

```text
Usuario habla
    -> STT externo
    -> Dialogflow ES
    -> Webhook FastAPI
    -> RAG con ChromaDB
    -> LLM
    -> TTS externo
    -> Respuesta en voz
```

---

## 2. Objetivos del proyecto / Ejercicio práctico

- Diseñar un agente conversacional en **Dialogflow ES** con intents, entidades, contextos y webhook.
- Integrar un sistema externo de **Speech-to-Text** para convertir audio a texto.
- Integrar un sistema externo de **Text-to-Speech** para convertir la respuesta en audio.
- Procesar documentos técnicos mediante **OCR**.
- Dividir el contenido extraído en chunks.
- Generar embeddings y almacenar la información en **ChromaDB**.
- Implementar un pipeline **RAG** para recuperar contexto relevante y generar respuestas con un LLM.
- Gestionar casos sin información suficiente evitando respuestas inventadas.
- Exponer una demo web local que permita probar el flujo completo por voz.

---

## 3. Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Agente conversacional | Dialogflow ES |
| Backend / Webhook | Python + FastAPI |
| Servidor ASGI | Uvicorn |
| STT | OpenAI STT (`gpt-4o-mini-transcribe` o equivalente) |
| TTS | OpenAI TTS (`gpt-4o-mini-tts` o equivalente) |
| OCR | Tesseract OCR |
| Procesamiento PDF | PyMuPDF |
| Base vectorial | ChromaDB |
| Embeddings | sentence-transformers |
| LLM | OpenAI |
| Exposición local a internet | ngrok |
| Interfaz demo | HTML + JavaScript servido desde FastAPI |

---

## 4. Estructura recomendada del proyecto

```text
ProyectoIAGenerativa/
│
├── app/
│   ├── config.py
│   ├── dialogflow_client.py
│   ├── main.py
│   ├── rag.py
│   ├── stt.py
│   ├── tts.py
│   ├── voice.py
│   └── webhook.py
│
├── scripts/
│   ├── ingest_documents.py
│   └── test_rag.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── vector_db/
│
├── credentials/
│   └── dialogflow-service-account.json
│
├── dialogflow/
│   └── agente_dialogflow_exportado.zip
│
├── docs/
│   └── informe.pdf
│
├── outputs/
│   ├── uploads/
│   └── respuesta_*.mp3
│
├── .env
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 5. Requisitos previos

### 5.1. Python

Se recomienda Python 3.10 o superior.

Comprobar versión:

```bash
python --version
```

### 5.2. Tesseract OCR en Linux/WSL

Instalar Tesseract y los idiomas español e inglés:

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
```

Comprobar instalación:

```bash
tesseract --version
which tesseract
```

Normalmente la ruta será:

```text
/usr/bin/tesseract
```

### 5.3. ngrok

Se utiliza para exponer el backend local y permitir que Dialogflow pueda llamar al webhook.

```bash
ngrok http 8000
```

---

## 6. Instalación

Crear entorno virtual:

```bash
python -m venv venv
```

Activarlo en Linux/WSL:

```bash
source venv/bin/activate
```

Activarlo en Windows PowerShell:

```powershell
.\venv\Scripts\Activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Si se instalan manualmente:

```bash
pip install fastapi uvicorn python-dotenv chromadb sentence-transformers pillow pytesseract pymupdf openai python-multipart google-cloud-dialogflow
```

Actualizar `requirements.txt`:

```bash
pip freeze > requirements.txt
```

---

## 7. Configuración de variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-4o-mini

OPENAI_STT_MODEL=gpt-4o-mini-transcribe
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=coral

VECTOR_DB_PATH=data/vector_db
COLLECTION_NAME=technical_docs

TESSERACT_CMD=/usr/bin/tesseract
OCR_LANG=spa+eng

DIALOGFLOW_PROJECT_ID=tu_project_id_de_google_cloud
DIALOGFLOW_LANGUAGE_CODE=es
GOOGLE_APPLICATION_CREDENTIALS=credentials/dialogflow-service-account.json
```

Importante: no subir el archivo `.env` ni el JSON de credenciales a GitHub.

Archivo `.gitignore` recomendado:

```gitignore
venv/
.env
credentials/
outputs/
__pycache__/
*.pyc
```

---

## 8. Configuración de Dialogflow ES

El agente de Dialogflow ES debe estar creado en español y contener al menos 12 intents personalizados.

### 8.1. Intents creados

| Intent | Tipo | Webhook |
|---|---|---|
| Saludo | Respuesta estática | No |
| Despedida | Respuesta estática | No |
| AyudaGeneral | Respuesta estática | No |
| ExplicarConcepto | Respuesta dinámica | Sí |
| BuscarEnDocumentacion | Respuesta dinámica | Sí |
| ResolverError | Respuesta dinámica | Sí |
| PedirEjemploCodigo | Respuesta dinámica | Sí |
| ConsultarComando | Respuesta dinámica | Sí |
| ConfirmarConsulta | Multi-turno | Opcional |
| CancelarConsulta | Respuesta estática | No |
| CambiarTema | Gestión de conversación | Opcional |
| VolverConsultaAnterior | Respuesta dinámica | Sí |

### 8.2. Entidades creadas

| Entidad | Tipo | Uso |
|---|---|---|
| `lenguaje_programacion` | Personalizada | Captura Python, Django, SQL, JavaScript, etc. |
| `tipo_consulta` | Personalizada | Captura error, concepto, comando, ejemplo, configuración, etc. |
| `codigo_error_regex` | Regexp entity | Captura patrones como HTTP 404, SQL-105, ModuleNotFoundError, etc. |

Ejemplos de expresiones regex:

```text
HTTP\s?\d{3}
ERR-\d{4}-\d{3}
SQL-\d+
[A-Za-z]+Error
[A-Za-z]+Exception
[A-Z]{2,5}-\d{3,6}
```

### 8.3. Fulfillment

En Dialogflow ES:

```text
Fulfillment -> Webhook -> Enabled
```

URL de ejemplo:

```text
https://TU_SUBDOMINIO_NGROK.ngrok-free.app/webhook/dialogflow
```

Cada intent dinámico debe tener activada la opción:

```text
Enable webhook call for this intent
```

---

## 9. Credenciales de Google Cloud para Dialogflow

Crear una cuenta de servicio en Google Cloud y asignarle permisos sobre el proyecto donde está el agente.

Roles recomendados:

- `Dialogflow API Client`
- o `Administrador de la API de Dialogflow`

Descargar la clave JSON y guardarla como:

```text
credentials/dialogflow-service-account.json
```

En Linux/WSL se puede exportar la variable si fuera necesario:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=credentials/dialogflow-service-account.json
```

---

## 10. Ingesta de documentos: OCR, chunks, embeddings y ChromaDB

Los documentos se colocan en:

```text
data/raw/
```

Ejemplos(rapidos sin mucha info esa documentacioon, la documentacion larga esta en "raw/large"):

```text
data/raw/documentacion_tecnica_demo_ocr.png
data/raw/apuntes_tecnicos.txt
```

Ejecutar la ingesta:

```bash
python -m scripts.ingest_documents --reset
```

El proceso realiza:

```text
Documento o imagen
    -> OCR o lectura de texto
    -> limpieza
    -> división en chunks
    -> generación de embeddings
    -> almacenamiento en ChromaDB
```

Salida esperada:

```text
Colección eliminada: technical_docs
Procesando: documentacion_tecnica_demo_ocr.png
Chunks añadidos: 1
Procesando: apuntes_tecnicos.txt
Chunks añadidos: 1
Ingesta terminada. Total chunks: 2
```

---

## 11. Prueba del RAG sin Dialogflow

Ejecutar:

```bash
python -m scripts.test_rag
```

También se puede probar una pregunta concreta desde el webhook local:

```bash
curl -X POST http://127.0.0.1:8000/webhook/dialogflow \
-H "Content-Type: application/json" \
-d '{
  "queryResult": {
    "queryText": "Qué es una API REST",
    "intent": {
      "displayName": "BuscarEnDocumentacion"
    },
    "parameters": {}
  }
}'
```

Respuesta esperada:

```json
{
  "fulfillmentText": "Una API REST permite comunicar aplicaciones mediante peticiones HTTP..."
}
```

---

## 12. Ejecución del backend

Arrancar FastAPI:

```bash
uvicorn app.main:app --reload
```

Comprobar estado:

```text
http://127.0.0.1:8000
```

Demo de voz:

```text
http://127.0.0.1:8000/voice
```

---

## 13. Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Comprueba estado del backend |
| POST | `/webhook/dialogflow` | Webhook llamado por Dialogflow ES |
| GET | `/voice` | Interfaz web de demostración por voz |
| POST | `/voice/chat` | Recibe audio, ejecuta STT, Dialogflow, RAG y TTS |

---

## 14. Estado del proyecto

Estado actual:

- Dialogflow ES configurado.
- Intents y entidades creados.
- Webhook FastAPI funcional.
- OCR con Tesseract funcionando.
- ChromaDB con documentos ingestados.
- RAG real operativo.
- STT y TTS externos integrados.
- Demo web por voz funcionando.

---

## 15. Mejoras futuras pensadas

- Añadir más documentos técnicos a la base de conocimiento.
- Mejorar el ranking de recuperación semántica.
- Añadir memoria conversacional persistente.
- Añadir interfaz web con historial de conversación.
- Integrar Telegram o Slack.
- Añadir logs detallados de evaluación.
- Añadir tests automáticos del pipeline RAG.
