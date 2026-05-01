import argparse
import io
import re
import uuid
from pathlib import Path

import chromadb
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    OCR_LANG,
    TESSERACT_CMD,
    VECTOR_DB_PATH,
)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp", ".txt"}


def configure_tesseract() -> None:
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Página\s+\d+", " ", text, flags=re.IGNORECASE)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if len(chunk) > 100:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def ocr_image(image: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(image, lang=OCR_LANG)
    except pytesseract.TesseractError:
        return pytesseract.image_to_string(image, lang="eng")


def extract_text_from_image(path: Path) -> str:
    image = Image.open(path).convert("RGB")
    return ocr_image(image)


def extract_text_from_pdf(path: Path) -> str:
    """
    Procesa cada página del PDF como imagen y aplica OCR.
    Esto nos sirve para demostrar OCR real, incluso si el PDF es escaneado.
    """
    document = fitz.open(path)
    extracted_pages = []

    for page_index, page in enumerate(document):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        page_text = ocr_image(image)

        if page_text.strip():
            extracted_pages.append(f"\n--- Página {page_index + 1} ---\n{page_text}")

    return "\n".join(extracted_pages)


def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text(path: Path) -> str:
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(path)

    if extension in {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"}:
        return extract_text_from_image(path)

    if extension == ".txt":
        return extract_text_from_txt(path)

    return ""


def get_collection(reset: bool = False):
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Colección eliminada: {COLLECTION_NAME}")
        except Exception:
            pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_documents(reset: bool = False) -> None:
    configure_tesseract()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    collection = get_collection(reset=reset)

    files = [
        file
        for file in RAW_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print("No hay documentos en data/raw.")
        return

    total_chunks = 0

    for file in files:
        print(f"Procesando: {file.name}")

        raw_text = extract_text(file)
        clean = clean_text(raw_text)

        if not clean:
            print(f"No se pudo extraer texto de: {file.name}")
            continue

        processed_file = PROCESSED_DIR / f"{file.stem}.txt"
        processed_file.write_text(clean, encoding="utf-8")

        chunks = chunk_text(clean)

        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            ids.append(str(uuid.uuid4()))
            documents.append(chunk)
            metadatas.append(
                {
                    "source": file.name,
                    "chunk": index,
                    "type": file.suffix.lower(),
                }
            )

        if documents:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

            total_chunks += len(documents)
            print(f"Chunks añadidos: {len(documents)}")

    print(f"Ingesta terminada. Total chunks: {total_chunks}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Recrear la colección desde cero")
    args = parser.parse_args()

    ingest_documents(reset=args.reset)