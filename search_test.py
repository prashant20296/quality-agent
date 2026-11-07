import chromadb
from chromadb.utils import embedding_functions

embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("ncr_records", embedding_function=embed_fn)

query = input("Describe a defect: ")
results = collection.query(query_texts=[query], n_results=3)

for doc, dist in zip(results["documents"][0], results["distances"][0]):
    print(f"\n--- distance {dist:.3f} ---\n{doc}")