import os, re, sqlite3
import chromadb
import datetime
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
    Call this ONLY after you have run the data queries and NCR search, and
    content must be the full report you wrote (sections D1 to D8), never the
    user's question. filename: short name without extension."""
    required = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
    missing = [d for d in required if d not in content]
    if len(content) < 800 or missing:
        return ("Report rejected: it must be a full 8D report (at least 800 "
                "characters) with sections D1 to D8, based on evidence from the "
                "tools. Missing: " + ", ".join(missing) + ". Investigate first, "
                "then call this tool again with the complete report.")
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", filename)
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{safe}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Report saved to {path}"

def _notes_conn():
    conn = sqlite3.connect("memory.db")
    conn.execute("CREATE TABLE IF NOT EXISTS notes "
                 "(id INTEGER PRIMARY KEY, created TEXT, note TEXT)")
    return conn

@tool
def remember_note(note: str) -> str:
    """Save a durable fact that the user explicitly asked you to remember,
    such as a confirmed root cause, a decision or a plant rule. Never use
    this for guesses or for anything the user did not ask to save."""
    conn = _notes_conn()
    conn.execute("INSERT INTO notes (created, note) VALUES (?, ?)",
                 (datetime.date.today().isoformat(), note))
    conn.commit()
    conn.close()
    return "Saved."

@tool
def recall_notes(topic: str) -> str:
    """Look up previously saved notes by a keyword (e.g. 'Welding Cell 2').
    Use this at the start of an investigation to check for earlier findings."""
    conn = _notes_conn()
    rows = conn.execute(
        "SELECT created, note FROM notes WHERE note LIKE ? ORDER BY id DESC LIMIT 10",
        (f"%{topic}%",)).fetchall()
    conn.close()
    if not rows:
        return "No saved notes on that topic."
    return "\n".join(f"[{d}] {n}" for d, n in rows)