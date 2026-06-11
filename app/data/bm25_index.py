import pickle

from rank_bm25 import BM25Okapi


with open("vectorstore/texts.pkl", "rb") as f:
    texts = pickle.load(f)

tokenized_corpus = [
    text.split() for text in texts
]

bm25 = BM25Okapi(tokenized_corpus)


def bm25_search(query, top_k=5):

    tokenized_query = query.split()

    scores = bm25.get_scores(tokenized_query)

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [idx for idx, _ in ranked[:top_k]]