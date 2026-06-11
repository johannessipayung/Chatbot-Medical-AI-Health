from sentence_transformers import CrossEncoder

reranker = CrossEncoder(
    "BAAI/bge-reranker-base"
)


def rerank(query, docs):

    pairs = [
        (query, doc["text"])
        for doc in docs
    ]

    scores = reranker.predict(pairs)

    scored = list(zip(docs, scores))

    scored.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [x[0] for x in scored]