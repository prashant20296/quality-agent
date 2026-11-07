import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

_embed = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)
_collection = chromadb.PersistentClient(path="chroma_db").get_collection(
    "ncr_records", embedding_function=_embed
)

@tool
def search_ncr(query: str) -> str:
    """Search past non-conformance reports (NCRs) from the plant's history.
    Use this whenever the user describes a defect, failure or quality problem,
    to find similar past cases with their root causes and corrective actions.
    The query should be a short description of the defect, part and process."""
    res = _collection.query(query_texts=[query], n_results=3)
    return "\n\n".join(res["documents"][0])