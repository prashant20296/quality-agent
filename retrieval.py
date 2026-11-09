import re
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

_embed = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)
_col = chromadb.PersistentClient(path="chroma_db").get_collection(
    "ncr_records", embedding_function=_embed
)

_data = _col.get(include=["documents"])
_ids = _data["ids"]
_docs = _data["documents"]
_doc_by_id = dict(zip(_ids, _docs))

def _tok(text):
    return re.findall(r"[a-z0-9\-]+", text.lower())

_bm25 = BM25Okapi([_tok(d) for d in _docs])
_reranker = None

def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker

def vector_search(query, k=10):
    res = _col.query(query_texts=[query], n_results=min(k, len(_ids)))
    return list(res["ids"][0])

def bm25_search(query, k=10):
    scores = _bm25.get_scores(_tok(query))
    order = sorted(range(len(_ids)), key=lambda i: scores[i], reverse=True)[:k]
    return [_ids[i] for i in order]

def hybrid_search(query, k=10, rrf_k=60):
    fused = {}
    for ranking in (vector_search(query, 20), bm25_search(query, 20)):
        for rank, id_ in enumerate(ranking):
            fused[id_] = fused.get(id_, 0) + 1.0 / (rrf_k + rank + 1)
    return sorted(fused, key=fused.get, reverse=True)[:k]

def hybrid_rerank(query, k=5, pool=10):
    candidates = hybrid_search(query, pool)
    scores = _get_reranker().predict([(query, _doc_by_id[i]) for i in candidates])
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked][:k]

def get_docs(ids):
    return [_doc_by_id[i] for i in ids]