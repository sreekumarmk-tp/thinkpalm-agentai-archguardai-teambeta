import streamlit as st
import os
import requests
import base64
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

# --- 1. LOAD SECRETS (From .env file) ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- 2. UI CONFIGURATION ---
st.set_page_config(page_title="Agentic Arch Reviewer", page_icon="🏗️", layout="wide")
st.title("🏗️ AI Architecture Review Assistant")

# Sidebar: Only Model Choice
with st.sidebar:
    st.header("Configuration")
    model_choice = st.selectbox("Select Model", [
	    "google/gemma-3-27b-it:free",       # Fallback 1 (Stable)
    	"openai/gpt-oss-120b:free",        # Fallback 2 (Strong reasoning)
    	"meta-llama/llama-3.3-70b-instruct:free", # Fallback 3 (Reliable)
    	"qwen/qwen3.6-plus:free"
    ])
    st.divider()
    st.caption("Backend powered by LangGraph & OpenRouter")

# Main Input
repo_url = st.text_input("Enter GitHub Repository URL", "https://github.com/arjunpkumar/flutter_base")

# --- 3. GITHUB UTILITIES ---
def fetch_repo_structure(repo_url):
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        tree = res.json().get("tree", [])
        files = [f["path"] for f in tree if f["type"] == "blob" and not any(x in f["path"] for x in ['.png', '.jpg', 'node_modules', '.git'])]
        return "\n".join(files[:100])
    except Exception as e:
        return f"Error fetching structure: {str(e)}"

def read_github_file(repo_url, path):
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return content[:5000] 
    except Exception as e:
        return f"Error reading file: {str(e)}"

# --- 4. AGENT EXECUTION ---
if st.button("Run Architecture Analysis"):
    if not OPENROUTER_API_KEY:
        st.error("API Key missing. Please set OPENROUTER_API_KEY in your .env file.")
        st.stop()

    # Initialize LLM
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        model=model_choice,
        temperature=0
    )

    # Define Tools
    tools = [
        Tool(
            name="list_repo_files",
            func=lambda x: fetch_repo_structure(repo_url),
            description="Use to see the file tree of the repo."
        ),
        Tool(
            name="read_specific_file",
            func=lambda path: read_github_file(repo_url, path),
            description="Use to read code content. Input: full file path."
        )
    ]

    # Initialize LangGraph ReAct Agent
    agent_executor = create_react_agent(llm, tools)

    with st.spinner(f"Analyzing via {model_choice}..."):
        task = {
            "messages": [
                ("user", f"Analyze the code structure of the repo at {repo_url}. "
                         "Generate the architecture report with recommendations.")
            ]
        }
        
        result = agent_executor.invoke(task)
        report = result["messages"][-1].content
        
        st.subheader("Architectural Analysis Report")
        st.markdown(report)