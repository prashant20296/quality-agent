import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # so chroma_db and inspection.db are found

from mcp.server.fastmcp import FastMCP
import tools as T

mcp = FastMCP("quality-tools")

@mcp.tool()
def search_ncr(query: str) -> str:
    """Search past non-conformance reports (NCRs) from the plant's history.
    Use this whenever the user describes a defect, failure or quality problem,
    to find similar past cases with their root causes and corrective actions.
    The query should be a short description of the defect, part and process."""
    return T.search_ncr.invoke({"query": query})

@mcp.tool()
def query_inspection_data(sql: str) -> str:
    """Run a read-only SQL SELECT query on the plant inspection database (SQLite).
    Table: inspections(id, date TEXT 'YYYY-MM-DD', station TEXT, part_name TEXT,
    shift TEXT 'A'/'B'/'C', inspected INTEGER, rejected INTEGER, defect_type TEXT).
    Stations: Welding Cell 1, Welding Cell 2, CNC-1, CNC-2, Paint Line,
    Assembly A, Hydraulic Test. Reject rate = SUM(rejected)*1.0/SUM(inspected).
    Use this for any question about counts, rates, trends, shifts or stations."""
    return T.query_inspection_data.invoke({"sql": sql})

if __name__ == "__main__":
    mcp.run()  # talks over stdio