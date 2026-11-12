import os

import pandas as pd
import requests
import streamlit as st

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")


st.set_page_config(page_title="CodeGenesis AI", page_icon="🧬", layout="wide")
st.title("🧬 CodeGenesis AI")
st.caption("Autonomous Multi-Agent Software Engineering Platform")

try:
    h = requests.get(f"{BACKEND}/health", timeout=3).json()
    st.sidebar.success(f"Backend OK · {h['model']}")
except Exception:
    st.sidebar.error("Backend not reachable. Run: uvicorn backend.main:app --reload")

st.sidebar.header("Repository")
mode = st.sidebar.radio("Source", ["GitHub URL", "ZIP upload"])
if mode == "GitHub URL":
    url = st.sidebar.text_input("https://github.com/owner/repo")
    if st.sidebar.button("Ingest") and url:
        with st.spinner("Cloning..."):
            r = requests.post(f"{BACKEND}/ingest/github", json={"url": url}, timeout=180)
        if r.ok:
            st.session_state["repo"] = r.json()
        else:
            st.sidebar.error(r.json().get("detail", r.text))
else:
    z = st.sidebar.file_uploader("ZIP", type="zip")
    if z and st.sidebar.button("Ingest"):
        r = requests.post(f"{BACKEND}/ingest/zip", files={"file": z.getvalue()}, timeout=180)
        if r.ok:
            st.session_state["repo"] = r.json()
        else:
            st.sidebar.error(r.json().get("detail", r.text))

repo = st.session_state.get("repo")
if not repo:
    st.info("Ingest a repository from the sidebar to begin.")
    st.stop()

rid = repo["repo_id"]
st.success(f"Repository loaded: `{rid}` · {len(repo['files'])} files")
tab_tree, tab_intel, tab_agents, tab_chat = st.tabs(
    ["📁 File tree", "🧠 Code intelligence", "🤖 AI agents", "💬 Chat"])

with tab_tree:
    st.dataframe(pd.DataFrame(repo["files"]), use_container_width=True)

with tab_intel:
    if st.button("Run code intelligence"):
        st.session_state["intel"] = requests.get(f"{BACKEND}/repo/{rid}/intel", timeout=120).json()
    intel = st.session_state.get("intel")
    if intel:
        st.subheader("Security findings (static)")
        st.dataframe(pd.DataFrame(intel["security_findings"]), use_container_width=True)
        st.subheader("Most complex functions")
        st.dataframe(pd.DataFrame(intel["most_complex"]), use_container_width=True)

with tab_agents:
    instr = st.text_area("Extra instructions (optional)")
    if st.button("Run multi-agent analysis"):
        with st.spinner("Agents working..."):
            r = requests.post(f"{BACKEND}/analyze", json={"repo_id": rid, "instructions": instr}, timeout=600)
        if r.ok:
            for name, text in r.json().items():
                with st.expander(name.replace("_", " ").title(), expanded=True):
                    st.markdown(text)
        else:
            st.error(r.text)

with tab_chat:
    q = st.text_input("Ask about this codebase")
    if st.button("Ask") and q:
        r = requests.post(f"{BACKEND}/chat", json={"repo_id": rid, "question": q}, timeout=300)
        st.markdown(r.json().get("answer", r.text))
