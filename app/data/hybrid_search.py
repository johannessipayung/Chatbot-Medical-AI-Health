import pickle
import faiss
import numpy as np

from sentence_transformers import (
    SentenceTransformer
)

from app.data.bm25_index import bm25_search

from app.services.reranker_service import (
    rerank
)

from app.config.settings import settings


embedding_model = SentenceTransformer(
    settings.EMBEDDING_MODEL
)

index = faiss.read_index(
    settings.FAISS_INDEX_PATH
)

with open(settings.TEXTS_PATH, "rb") as f:
    texts = pickle.load(f)

with open(settings.METADATA_PATH, "rb") as f:
    metadatas = pickle.load(f)


class HybridSearch:

    def dense_search(
        self,
        query: str,
        top_k: int = 5
    ):

        query_embedding = embedding_model.encode(
            [query],
            convert_to_numpy=True
        )

        distances, indices = index.search(
            query_embedding,
            top_k
        )

        dense_results = []

        for idx, score in zip(
            indices[0],
            distances[0]
        ):

            dense_results.append({
                "text": texts[idx],
                "metadata": metadatas[idx],
                "score": float(score),
                "retrieval_type": "dense"
            })

        return dense_results

    def bm25_retrieve(
        self,
        query: str,
        top_k: int = 5
    ):

        bm25_indices = bm25_search(
            query,
            top_k=top_k
        )

        bm25_results = []

        for idx in bm25_indices:

            bm25_results.append({
                "text": texts[idx],
                "metadata": metadatas[idx],
                "score": 1.0,
                "retrieval_type": "bm25"
            })

        return bm25_results

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5
    ):

        dense_results = self.dense_search(
            query,
            top_k=top_k
        )

        bm25_results = self.bm25_retrieve(
            query,
            top_k=top_k
        )

        combined_docs = {}

        # DENSE RESULTS

        for doc in dense_results:

            key = (
                doc["metadata"]["source"],
                doc["metadata"]["page"]
            )

            combined_docs[key] = doc

        # BM25 RESULTS

        for doc in bm25_results:

            key = (
                doc["metadata"]["source"],
                doc["metadata"]["page"]
            )

            if key not in combined_docs:

                combined_docs[key] = doc

        merged_docs = list(
            combined_docs.values()
        )

        # RERANK

        reranked_docs = rerank(
            query,
            merged_docs
        )

        return reranked_docs[:top_k]