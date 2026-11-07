import json
import chromadb
from chromadb.utils import embedding_functions

# 1. Load the NCR records
with open("data/ncr_records.json", encoding="utf-8") as f:
    records = json.load(f)

# 2. Embedding model (local, free)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)

# 3. Persistent vector database
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(
    name="ncr_records", embedding_function=embed_fn
)

# 4. Turn each NCR into one text chunk + metadata
ids, docs, metas = [], [], []
for r in records:
    text = (
        f"NCR {r['ncr_id']} | Area: {r['area']} | Part: {r['part_name']}\n"
        f"Defect: {r['defect_description']}\n"
        f"Root cause: {r['root_cause']}\n"
        f"Corrective action: {r['corrective_action']}\n"
        f"Preventive action: {r['preventive_action']}"
    )
    ids.append(r["ncr_id"])
    docs.append(text)
    metas.append({"area": str(r["area"]), "part_name": str(r["part_name"])})

collection.upsert(ids=ids, documents=docs, metadatas=metas)
print("Stored", collection.count(), "NCRs")