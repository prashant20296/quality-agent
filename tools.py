import os, re, sqlite3
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

@tool
def query_inspection_data(sql: str) -> str:
    """Run a read-only SQL SELECT query on the plant inspection database (SQLite).
    Table: inspections(id, date TEXT 'YYYY-MM-DD', station TEXT, part_name TEXT,
    shift TEXT 'A'/'B'/'C', inspected INTEGER, rejected INTEGER, defect_type TEXT).
    Stations: Welding Cell 1, Welding Cell 2, CNC-1, CNC-2, Paint Line,
    Assembly A, Hydraulic Test. Reject rate = SUM(rejected)*1.0/SUM(inspected).
    Use this for any question about counts, rates, trends, shifts or stations."""
    if not sql.strip().lower().startswith("select"):
        return "Only SELECT queries are allowed."
    try:
        conn = sqlite3.connect("file:inspection.db?mode=ro", uri=True)
        cur = conn.execute(sql)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchmany(50)
        conn.close()
        if not rows:
            return "Query returned no rows."
        lines = [" | ".join(cols)] + [" | ".join(str(v) for v in r) for r in rows]
        return "\n".join(lines)
    except Exception as e:
        return f"SQL error: {e}"

@tool
def save_8d_report(filename: str, content: str) -> str:
    """Save a finished 8D report draft as a markdown file in the reports folder.
    Use this only after the analysis is complete and the user asked for a report.
    filename: short name without extension, e.g. 'welding_cell2_8d'.
    content: the full report text in markdown."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", filename)
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{safe}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Report saved to {path}"