import asyncio, sys
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    client = MultiServerMCPClient({
        "quality": {"command": sys.executable, "args": ["mcp_server.py"],
                    "transport": "stdio"}
    })
    tools = await client.get_tools()
    print("Tools found:", [t.name for t in tools])
    search = next(t for t in tools if t.name == "search_ncr")
    print(await search.ainvoke({"query": "weld penetration problem"}))

asyncio.run(main())