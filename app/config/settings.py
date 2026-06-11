from dotenv import load_dotenv
import os

load_dotenv()


class Settings:

    # =========================
    # API CONFIG
    # =========================

    MAIA_API_KEY = os.getenv(
        "MAIA_API_KEY",
        "sk-DXoeY8zEzPZHr_YaBEwWiA"
    )

    MAIA_BASE_URL = os.getenv(
        "MAIA_BASE_URL",
        "https://api.maiarouter.ai/v1"
    )

    MODEL_NAME = os.getenv(
        "MODEL_NAME",
        "maia/gemini-3.1-flash-lite-preview"
    )

    # =========================
    # VECTORSTORE
    # =========================

    VECTORSTORE_DIR = "vectorstore"

    FAISS_INDEX_PATH = (
        f"{VECTORSTORE_DIR}/faiss.index"
    )

    TEXTS_PATH = (
        f"{VECTORSTORE_DIR}/texts.pkl"
    )

    METADATA_PATH = (
        f"{VECTORSTORE_DIR}/metadatas.pkl"
    )

    # =========================
    # EMBEDDING
    # =========================

    EMBEDDING_MODEL = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    RERANKER_MODEL = (
        "BAAI/bge-reranker-base"
    )

    # =========================
    # RETRIEVAL
    # =========================

    TOP_K_RETRIEVAL = 5

    BM25_WEIGHT = 0.4

    DENSE_WEIGHT = 0.6

    # =========================
    # CONFIDENCE
    # =========================

    HIGH_CONFIDENCE = 0.85

    MEDIUM_CONFIDENCE = 0.65

    LOW_CONFIDENCE = 0.40

    # =========================
    # INPUT LIMITS
    # =========================

    MAX_QUESTION_CHARS = int(
        os.getenv("MAX_QUESTION_CHARS", "4000")
    )

    # =========================
    # TOKEN ESTIMATION
    # =========================

    # Default pricing for maia/gemini-3-flash-preview
    # Based on the provided price sheet: $0.50 / 1M input tokens, $3.00 / 1M output tokens.
    INPUT_TOKEN_PRICE_PER_1M = float(
        os.getenv("INPUT_TOKEN_PRICE_PER_1M", "0.50")
    )
    OUTPUT_TOKEN_PRICE_PER_1M = float(
        os.getenv("OUTPUT_TOKEN_PRICE_PER_1M", "3.00")
    )

    # Backward-compatible fallback for old estimators.
    TOKEN_PRICE_PER_1K = float(
        os.getenv("TOKEN_PRICE_PER_1K", "0.0015")
    )

    # =========================
    # MEDICAL DISCLAIMER
    # =========================

    DISCLAIMER = """
AI ini bukan pengganti dokter profesional.
Jika kondisi darurat, segera hubungi 119 atau IGD terdekat.
"""
    

settings = Settings()