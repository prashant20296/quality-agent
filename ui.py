import asyncio, threading, uuid
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from agent import build_app, text_of

st.set_page_config(page_title="Quality Agent", page_icon="🔧")

@st.cache_resource
def get_runtime():
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    app, _ = asyncio.run_coroutine_threadsafe(build_app(), loop).result()
    return loop, app

loop, app = get_runtime()

def ask(question, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    fut = asyncio.run_coroutine_threadsafe(
        app.ainvoke({"messages": [("user", question)]}, config), loop)
    msgs = fut.result()["messages"]
    last_user = max(i for i, m in enumerate(msgs) if isinstance(m, HumanMessage))
    tools_used = [tc["name"] for m in msgs[last_user:]
                  if isinstance(m, AIMessage) for tc in m.tool_calls]
    return text_of(msgs[-1]), tools_used

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.chat = []

st.title("🔧 Quality Investigator Agent")
st.caption("Synthetic plant data only. Reports are drafts, never records.")

with st.sidebar:
    if st.button("New conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat = []
        st.rerun()

for role, text, tools in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(text)
        if tools:
            st.caption("Tools used: " + ", ".join(tools))

if q := st.chat_input("Describe a defect or ask a data question"):
    st.session_state.chat.append(("user", q, []))
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("Investigating..."):
            try:
                answer, tools = ask(q, st.session_state.thread_id)
            except Exception as e:
                answer, tools = f"Error: {str(e)[:300]}", []
        st.markdown(answer)
        if tools:
            st.caption("Tools used: " + ", ".join(tools))
    st.session_state.chat.append(("assistant", answer, tools))