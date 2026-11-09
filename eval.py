import asyncio, json, re, sqlite3, sys, time, uuid
from langchain_core.messages import AIMessage
from agent import build_app, text_of

with open("data/ncr_records.json", encoding="utf-8") as f:
    KNOWN_IDS = {r["ncr_id"] for r in json.load(f)}

def total_inspected(station):
    conn = sqlite3.connect("inspection.db")
    v = conn.execute("SELECT SUM(inspected) FROM inspections WHERE station=?",
                     (station,)).fetchone()[0]
    conn.close()
    return str(v)

NO_DATA_PHRASES = ["no similar", "no relevant", "not find", "couldn't find",
                   "did not find", "no past", "no matching", "no record", "nothing"]

CASES = [
    {"q": "Which shift at Welding Cell 2 has the highest reject rate since 2026-10-11?",
     "tools_any": ["query_inspection_data"], "include": ["shift c", "7.8"]},
    {"q": "What is an 8D report?",
     "forbid": ["query_inspection_data", "search_ncr", "save_8d_report"]},
    {"q": "Hydraulic hose is leaking at the fitting in end-of-line test, what could be the cause?",
     "tools_any": ["search_ncr"], "include": ["NCR-2026-004"]},
    {"q": "Cracks appearing in the cab glass during assembly",
     "include_any": NO_DATA_PHRASES},
    {"q": "How many units were inspected in total at CNC-1?",
     "tools_any": ["query_inspection_data"], "include": [total_inspected("CNC-1")]},
]

def check(case, answer, tools_called):
    problems = []
    a = answer.lower().replace(",", "")
    for s in case.get("include", []):
        if s.lower() not in a:
            problems.append(f"missing '{s}'")
    if case.get("include_any") and not any(s in a for s in case["include_any"]):
        problems.append("none of the expected 'nothing found' phrases appear")
    if case.get("tools_any") and not set(case["tools_any"]) & set(tools_called):
        problems.append(f"expected one of {case['tools_any']}, got {tools_called}")
    bad = set(case.get("forbid", [])) & set(tools_called)
    if bad:
        problems.append(f"used tools it should not have: {sorted(bad)}")
    invented = set(re.findall(r"NCR-\d{4}-\d+", answer)) - KNOWN_IDS
    if invented:
        problems.append(f"invented NCR IDs: {sorted(invented)}")
    return problems

async def main():
    app, _ = await build_app()
    picks = [int(x) for x in sys.argv[1:]] or list(range(1, len(CASES) + 1))
    ran = passed = 0
    for i in picks:
        case = CASES[i - 1]
        config = {"configurable": {"thread_id": f"eval-{uuid.uuid4()}"}}
        try:
            result = await app.ainvoke({"messages": [("user", case["q"])]}, config)
        except Exception as e:
            print(f"[{i}] ERROR, not scored: {str(e)[:150]}")
            continue
        msgs = result["messages"]
        tools_called = [tc["name"] for m in msgs if isinstance(m, AIMessage)
                        for tc in m.tool_calls]
        answer = text_of(msgs[-1])
        problems = check(case, answer, tools_called)
        ran += 1
        if problems:
            print(f"[{i}] FAIL  {case['q'][:60]}")
            for p in problems:
                print("      -", p)
            print("      answer starts:", answer[:200].replace("\n", " "))
        else:
            passed += 1
            print(f"[{i}] PASS  {case['q'][:60]}")
        time.sleep(3)
    print(f"\nScore: {passed}/{ran} scored cases passed")

if __name__ == "__main__":
    asyncio.run(main())