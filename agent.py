import os, sys, asyncio
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from tools import save_8d_report, remember_note, recall_notes

load_dotenv()

SYSTEM = SystemMessage(content=(
    "You are a senior quality engineer assistant for a tractor plant. "
    "Tools: search_ncr (past NCRs), query_inspection_data (SQL on inspection "
    "results), save_8d_report, recall_notes, remember_note. "
    "For data questions, query the database; use MAX(date) as 'today' for recent "
    "periods. Work in order: station-level data, then drill down by shift and "
    "date, then search past NCRs, and only then write any report. "
    "Only cite NCR IDs and numbers that appear in tool results; never invent them. "
    "8D reports use sections D1 to D8. Never state that any action has been "
    "completed or implemented; write all actions as 'Proposed'. Do not invent "
    "dates, names or team roles; write 'TBD'. Only facts from tool results are "
    "verified; everything else is a hypothesis. Never claim a root cause was "
    "confirmed. Never call save_8d_report with the user's question as content. "
    "Use recall_notes when starting an investigation. Use remember_note only when "
    "the user explicitly asks you to remember something; saved notes are the "
    "user's statements, not verified fact."
))

class State(TypedDict):
    messages: Annotated[list, add_messages]

def text_of(msg):
    c = msg.content
    if isinstance(c, list):
        return "".join(p.get("text", "") for p in c if isinstance(p, dict))
    return c

async def build_app():
    client = MultiServerMCPClient({
        "quality": {"command": sys.executable, "args": ["mcp_server.py"],
                    "transport": "stdio"}
    })
    mcp_tools = await client.get_tools()
    tools = mcp_tools + [save_8d_report, remember_note, recall_notes]

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    ).bind_tools(tools)

    async def agent_node(state: State):
        return {"messages": [await llm.ainvoke([SYSTEM] + state["messages"])]}

    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=MemorySaver()), [t.name for t in mcp_tools]

async def main():
    app, mcp_names = await build_app()
    print("Tools loaded from MCP server:", mcp_names)
    config = {"configurable": {"thread_id": "session-1"}}
    while True:
        q = input("\nYou (q to quit): ")
        if q.strip().lower() == "q":
            break
        result = await app.ainvoke({"messages": [("user", q)]}, config)
        msgs = result["messages"]
        last_user = max(i for i, m in enumerate(msgs) if isinstance(m, HumanMessage))
        for m in msgs[last_user:]:
            if isinstance(m, AIMessage) and m.tool_calls:
                for tc in m.tool_calls:
                    print(f"[agent called {tc['name']} with {tc['args']}]")
        print("\nAgent:", text_of(msgs[-1]))

if __name__ == "__main__":
    asyncio.run(main())