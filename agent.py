import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from tools import search_ncr

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
)
tools = [search_ncr]
llm_with_tools = llm.bind_tools(tools)

SYSTEM = SystemMessage(content=(
    "You are a senior quality engineer assistant for a tractor plant. "
    "When the user describes a defect, first search past NCRs. Then give: "
    "(1) similar past cases with NCR IDs, (2) likely root causes using the "
    "past evidence, (3) suggested containment and corrective actions. "
    "Only cite NCRs that appear in tool results. If nothing relevant is "
    "found, say so instead of guessing."
))

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent_node(state: State):
    return {"messages": [llm_with_tools.invoke([SYSTEM] + state["messages"])]}

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition)  # tool call? -> tools, else end
graph.add_edge("tools", "agent")
app = graph.compile()

def text_of(msg):
    c = msg.content
    if isinstance(c, list):
        return "".join(p.get("text", "") for p in c if isinstance(p, dict))
    return c

if __name__ == "__main__":
    while True:
        q = input("\nYou (q to quit): ")
        if q.strip().lower() == "q":
            break
        result = app.invoke({"messages": [("user", q)]})
        for m in result["messages"]:
            if isinstance(m, AIMessage) and m.tool_calls:
                for tc in m.tool_calls:
                    print(f"[agent called {tc['name']} with {tc['args']}]")
        print("\nAgent:", text_of(result["messages"][-1]))