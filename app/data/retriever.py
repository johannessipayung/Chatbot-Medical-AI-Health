import pickle
import faiss

from sentence_transformers import SentenceTransformer

from app.data.bm25_index import bm25_search
from app.services.reranker_service import rerank
from app.services.document_meta_service import DocumentMetaService


from app.config.settings import settings

embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

index = faiss.read_index(
    "vectorstore/faiss.index"
)

with open("vectorstore/texts.pkl", "rb") as f:
    texts = pickle.load(f)

with open("vectorstore/metadatas.pkl", "rb") as f:
    metadatas = pickle.load(f)


class MedicalRetriever:

    def search(self, query, top_n=5):

        dense_embedding = embedding_model.encode(
            [query],
            convert_to_numpy=True
        )

        distances, dense_indices = index.search(
            dense_embedding,
            top_n
        )

        bm25_indices = bm25_search(query, top_k=top_n)

        combined = list(set(
            dense_indices[0].tolist() +
            bm25_indices
        ))

        docs = []

        for idx in combined:

            meta = DocumentMetaService.enrich(metadatas[idx])
            docs.append({
                "text": texts[idx],
                "metadata": meta
            })

        reranked = rerank(query, docs)

        formatted_docs = []

        for doc in reranked[:top_n]:

            source = doc["metadata"]["source"]
            page = doc["metadata"]["page"]
            year = doc["metadata"].get("year")
            authority = doc["metadata"].get("authority")

            formatted_docs.append(
                f"""
SOURCE: {source}
PAGE: {page}
YEAR: {year}
AUTHORITY: {authority}

CONTENT:
{doc['text']}
"""
            )

        return formatted_docs

    def search_dense(self, query, top_n=5):
        dense_embedding = embedding_model.encode([query], convert_to_numpy=True)
        distances, dense_indices = index.search(dense_embedding, top_n)

        formatted_docs = []
        for idx in dense_indices[0].tolist():
            meta = DocumentMetaService.enrich(metadatas[idx])
            formatted_docs.append(
                f"""
SOURCE: {meta.get('source')}
PAGE: {meta.get('page')}
YEAR: {meta.get('year')}
AUTHORITY: {meta.get('authority')}

CONTENT:
{texts[idx]}
"""
            )
        return formatted_docs

    def search_bm25(self, query, top_n=5):
        bm25_indices = bm25_search(query, top_k=top_n)

        formatted_docs = []
        for idx in bm25_indices:
            meta = DocumentMetaService.enrich(metadatas[idx])
            formatted_docs.append(
                f"""
SOURCE: {meta.get('source')}
PAGE: {meta.get('page')}
YEAR: {meta.get('year')}
AUTHORITY: {meta.get('authority')}

CONTENT:
{texts[idx]}
"""
            )
        return formatted_docs
