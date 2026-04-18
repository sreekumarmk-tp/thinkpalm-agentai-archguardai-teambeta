import sys
import os
from pathlib import Path

# Add project root to sys.path to handle 'src' imports when running via streamlit
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import time
import json
from uuid import uuid4
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Set

import streamlit as st
from dotenv import load_dotenv

from src.config.settings import (
    OPENROUTER_API_KEY,
    AGENT_DEFINITIONS,
    OPENROUTER_ANY_FREE_SENTINEL,
    GROQ_MODELS,
    OPENROUTER_MODELS,
)
from src.tools.github import parse_github_repo
from src.utils.models import (
    fetch_available_free_models,
    get_model_candidates_for_agent,
    select_model_for_agent,
    fetch_available_free_models,
)
from src.memory.manager import (
    initialize_memory,
    build_memory_context,
    record_analysis_memory,
)
from src.agents.specialist import run_specialist_agent_with_retries
from src.agents.synthesizer import synthesize_report
from src.utils.rendering import display_enriched_report
from src.ui.components import render_sidebar, build_json_export, render_export_downloads

load_dotenv()

def apply_custom_styles():
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .main-title {
            font-size: 3rem !important;
            font-weight: 800 !important;
            background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem !important;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,201,255,0.3);
        }
        .report-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

def render_streamlit_app() -> None:
    st.set_page_config(page_title="ArchGuard AI", page_icon="🛡️", layout="wide")
    apply_custom_styles()
    
    st.markdown('<h1 class="main-title">🛡️ ArchGuard AI</h1>', unsafe_allow_html=True)
    st.markdown("#### *Autonomous Multi-Agent Architecture Review & Risk Guardrail*")
    st.divider()

    initialize_memory()

    config = render_sidebar()
    
    auto_pick_models = config["auto_pick_models"]
    run_in_parallel = config["run_in_parallel"]
    max_parallel_workers = config["max_parallel_workers"]
    max_attempts_per_model = config["max_attempts_per_model"]
    base_backoff_seconds = config["base_backoff_seconds"]
    active_preset = config["active_preset"]
    provider = config["llm_provider"]

    # Compact Model Selection in Sidebar
    with st.sidebar:
        st.subheader("🤖 Model Control")
        model_options = []
        if provider == "Groq":
            model_options = [f"groq/{m}" for m in GROQ_MODELS]
        else:
            model_options = [OPENROUTER_ANY_FREE_SENTINEL] + [f"openrouter/{m}" for m in OPENROUTER_MODELS]
            
        manual_model = st.selectbox(
            "Primary / Fallback Model",
            model_options,
            help="If auto-selection is off, this model is used. If on, it's the final fallback.",
            label_visibility="collapsed"
        )
        
    col_input, col_action = st.columns([4, 1])
    with col_input:
        repo_url = st.text_input(
            "Target Repository URL",
            placeholder="https://github.com/owner/repo",
            label_visibility="collapsed"
        )
    with col_action:
        run_analysis = st.button("🚀 Analyze Now", use_container_width=True, type="primary")

    if run_analysis:
        if not repo_url or repo_url == "https://github.com/<GitHubUserName>/<RepositoryName>":
            st.warning("Please enter a valid GitHub repository URL.")
            st.stop()

        from src.config.settings import GROQ_API_KEY
        if not OPENROUTER_API_KEY and not GROQ_API_KEY:
            st.error("API Keys missing. Set OPENROUTER_API_KEY or GROQ_API_KEY in your .env file.")
            st.stop()

        try:
            parse_github_repo(repo_url)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        with st.spinner("⚡ Initializing agents and discovering free model capacity..."):
            available_free_models = (
                fetch_available_free_models()
                if auto_pick_models or manual_model == OPENROUTER_ANY_FREE_SENTINEL
                else set()
            )

        specialist_results: Dict[str, str] = {}
        selected_models: Dict[str, str] = {}
        memory_context = build_memory_context(st.session_state.analysis_memory)
        
        progress_container = st.container()
        with progress_container:
            progress = st.progress(0)
            status = st.empty()

        total_steps = len(AGENT_DEFINITIONS) + 1
        model_plan: List[Tuple[Dict[str, str], List[str]]] = []
        for spec in AGENT_DEFINITIONS:
            candidates = (
                get_model_candidates_for_agent(spec["id"], available_free_models, manual_model)
                if auto_pick_models
                else (sorted(available_free_models) if manual_model == OPENROUTER_ANY_FREE_SENTINEL else [manual_model])
            )
            selected_models[spec["title"]] = candidates[0]
            model_plan.append((spec, candidates))

        if run_in_parallel:
            status.info(f"🛰️ Executing {len(AGENT_DEFINITIONS)} agents in parallel swarm...")
            completed = 0
            workers = min(max_parallel_workers, len(model_plan))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(
                        run_specialist_agent_with_retries,
                        repo_url,
                        spec,
                        candidates,
                        max_attempts_per_model,
                        float(base_backoff_seconds),
                        memory_context,
                    ): (spec, candidates)
                    for spec, candidates in model_plan
                }
                for future in as_completed(futures):
                    spec, candidates = futures[future]
                    try:
                        content, used_model = future.result()
                        specialist_results[spec["title"]] = content
                        selected_models[spec["title"]] = used_model
                    except Exception as exc:
                        status.error(f"❌ FATAL: Agent '{spec['title']}' failed. Swarm terminated.")
                        st.error(f"Reason: {str(exc)}")
                        executor.shutdown(wait=False, cancel_futures=True)
                        st.stop()

                    completed += 1
                    status.info(f"✅ Completed Swarm Task {completed}/{len(AGENT_DEFINITIONS)}: {spec['title']}")
                    progress.progress(completed / total_steps)
        else:
            for index, (spec, candidates) in enumerate(model_plan, start=1):
                status.info(f"🧬 Sequencing Agent {index}/{len(AGENT_DEFINITIONS)}: {spec['title']}...")
                try:
                    content, used_model = run_specialist_agent_with_retries(
                        repo_url,
                        spec,
                        candidates,
                        max_attempts_per_model,
                        float(base_backoff_seconds),
                        memory_context,
                    )
                    specialist_results[spec["title"]] = content
                    selected_models[spec["title"]] = used_model
                except Exception as exc:
                    status.error(f"❌ FATAL: Agent '{spec['title']}' failed.")
                    st.error(f"Reason: {str(exc)}")
                    st.stop()
                progress.progress(index / total_steps)

        synthesizer_model = (
            select_model_for_agent("report_synthesizer", available_free_models, provider=provider)
            if auto_pick_models
            else manual_model
        )
        status.info(f"💎 Synthesizing Final Analysis with {synthesizer_model}...")
        try:
            final_report = synthesize_report(
                repo_url,
                synthesizer_model,
                specialist_results,
                memory_context,
                max_attempts_per_model=max_attempts_per_model,
                base_backoff_seconds=float(base_backoff_seconds),
            )
        except Exception as exc:
            final_report = (
                "# Synthesis Partial Failure\n\n"
                f"Warning: Final synthesis failed. Showing raw specialist outputs only.\n\n"
                f"**Error Details:** {str(exc)}\n\n"
                + "\n\n".join([f"## {k}\n{v}" for k, v in specialist_results.items()])
            )

        progress.progress(1.0)
        status.success("✨ Analysis Completed Successfully.")
        
        run_id = str(uuid4())
        generated_at = datetime.now(timezone.utc).isoformat()
        record_analysis_memory(run_id, repo_url, generated_at, final_report)

        st.divider()
        st.header("📋 Analysis Report")
        
        tab_report, tab_raw, tab_export = st.tabs(["🚀 Executive Summary", "🔍 Specialist Intel", "📦 Export & Data"])
        
        with tab_report:
            render_export_downloads(final_report, run_id)
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            display_enriched_report(final_report)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab_raw:
            for title, out in specialist_results.items():
                with st.expander(f"📡 {title}", expanded=False):
                    st.info(f"**Agent Model:** `{selected_models[title]}`")
                    st.markdown(out)

        with tab_export:
            json_str = build_json_export(
                repo_url, run_id, generated_at, active_preset,
                run_in_parallel, max_parallel_workers, max_attempts_per_model,
                base_backoff_seconds, selected_models, synthesizer_model,
                specialist_results, final_report
            )
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="💾 Download JSON Data",
                    data=json_str,
                    file_name=f"arch_review_{run_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col_d2:
                # Add another copy of word/pdf here for convenience
                render_export_downloads(final_report, run_id)
                
            st.subheader("Raw JSON Context")
            st.json(json.loads(json_str))

if __name__ == "__main__":
    render_streamlit_app()