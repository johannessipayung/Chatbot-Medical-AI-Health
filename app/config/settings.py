from dotenv import load_dotenv
import os

load_dotenv()


class Settings:


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



    EMBEDDING_MODEL = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    RERANKER_MODEL = (
        "BAAI/bge-reranker-base"
    )

    TOP_K_RETRIEVAL = 5

    BM25_WEIGHT = 0.4

    DENSE_WEIGHT = 0.6

    

settings = Settings()