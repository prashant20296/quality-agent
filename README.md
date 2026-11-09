Quality Investigator Agent

An agentic AI assistant that helps a quality engineer investigate manufacturing defects. It searches past non-conformance reports (NCRs) with RAG, analyses inspection data with read-only SQL, and drafts 8D reports, using only evidence returned by its tools.

Personal learning project. All data is synthetic. No employer, supplier or production data is used. Generated reports are drafts for an engineer to review, never quality records.

Chat UI

What it does
Finds similar past NCRs by meaning (vector search), not just keywords
Answers data questions ("which shift has the highest reject rate?") by writing read-only SQL
Chains tools for an investigation: station, then shift, then date, then past NCRs
Drafts an 8D report (D1 to D8) with unverified items marked as hypotheses
Remembers context within a conversation and saves notes across sessions
Shows which tools it used for every answer
Architecture
MCP tool calls
User: Streamlit UI or CLI
LangGraph agent (Gemini)
MCP server: quality-tools
search_ncr: ChromaDB +bge-small embeddings
query_inspection_data:SQLite, read-only
Local tools
save_8d_report: validatedmarkdown output
remember_note /recall_notes: SQLite
MemorySaver: short-termchat memory

The agent runs a reason, act, observe loop: the model decides whether to answer or call a tool, reads the tool result, and decides again until it has enough evidence.

Tech stack and why
Part	Choice	Why
LLM	Gemini (free tier)	Free, supports tool calling; model name is set in .env so it is easy to swap
Agent framework	LangGraph	Explicit state graph, visible tool loop, built-in checkpointing
Embeddings	BAAI/bge-small-en-v1.5	Free, small, runs locally, no data leaves the machine
Vector DB	ChromaDB	Local and zero setup; one chunk per NCR record
Structured data	SQLite	Exact calculations for rates and counts, which RAG cannot do
Tool protocol	MCP (stdio)	NCR search and SQL run as a separate server any MCP client can reuse
Memory	LangGraph checkpointer + SQLite notes	Short-term chat context and long-term saved notes
UI	Streamlit	Fast chat UI in Python
Safety design
SQL tool opens the database read-only and accepts only SELECT
Report tool rejects incomplete reports (too short or missing D1 to D8), so the agent must investigate and retry
System prompt forbids invented NCR IDs, dates, names or completed actions; all actions are written as "Proposed" and unknowns as "TBD"
Long-term notes are only saved when the user explicitly asks, and are treated as user statements, not verified facts
The evaluation checks that every NCR ID the agent cites exists in the data
Project structure
agent.py              LangGraph agent, MCP client, CLI chat loop
mcp_server.py         MCP server exposing search_ncr and query_inspection_data
tools.py              Tool implementations (search, SQL, report, notes)
ui.py                 Streamlit chat interface
ingest.py             Loads NCRs into ChromaDB
make_inspection_db.py Builds the synthetic inspection database
generate_ncr.py       Generates synthetic NCRs with an LLM (optional)
eval.py               Agent evaluation harness (5 cases)
test_tools.py         Tests tools directly, no LLM calls
test_mcp.py           Tests the MCP server connection
data/ncr_records.json Synthetic NCR dataset
Run it

Requires Python 3.12 and a free Gemini API key from https://aistudio.google.com/apikey.

git clone https://github.com/prashant20296/quality-agent.git
cd quality-agent
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then add your API key to .env
python make_inspection_db.py
python ingest.py
streamlit run ui.py         # or: python agent.py for the CLI
Evaluation

python eval.py runs 5 cases:

A data question with a known answer (worst shift at a station)
A definition that should use no tools
A defect description that should retrieve a specific NCR
A defect with no match, where the agent must say nothing was found
A count checked against the database

Each case also checks that any cited NCR ID exists in the dataset.

Latest results: add your real run here (date, model, score), for example "5/5 passed on <date> with <model>".

Evaluation output

Checks are keyword-based and the model is not deterministic, so a pass is a good sign, not proof, and a failure needs human review.

Limitations
Synthetic data, so findings do not reflect a real plant
The planted anomaly (one welding cell, one shift) is deliberately easy to find
Free-tier LLM limits (requests per day) restrict how much can be tested
Plain vector search; no keyword matching or reranking yet
The report tool saves directly; there is no human approval step yet
Runs locally only; not deployed
Root causes are hypotheses; the agent cannot verify anything on the shop floor
Roadmap
 Hybrid retrieval and reranking: BM25 + vector search with rank fusion and a cross-encoder reranker, compared against plain vector search with a retrieval evaluation (Hit@k, MRR)
 Human approval before saving: pause the agent before save_8d_report so a person can approve, edit or reject the draft
 Deployment: containerise and deploy to the cloud, with secrets in a key vault and access control
 Production design on Azure: Azure OpenAI, Azure AI Search, Entra ID and Purview, with security trimming per user
