import json
import streamlit as st
import io
from typing import Dict
from src.utils.export import export_to_docx, export_to_pdf

def build_json_export(
    repo_url: str,
    run_id: str,
    generated_at_utc: str,
    active_preset: str,
    run_in_parallel: bool,
    max_parallel_workers: int,
    max_attempts_per_model: int,
    base_backoff_seconds: int,
    selected_models: Dict[str, str],
    synthesizer_model: str,
    specialist_results: Dict[str, str],
    final_report: str,
) -> str:
    payload = {
        "repository": repo_url,
        "run_metadata": {
            "run_id": run_id,
            "generated_at_utc": generated_at_utc,
        },
        "run_configuration": {
            "preset": active_preset.lower(),
            "parallel_enabled": run_in_parallel,
            "parallel_workers": max_parallel_workers,
            "retry_attempts_per_model": max_attempts_per_model,
            "base_backoff_seconds": base_backoff_seconds,
        },
        "models": {
            "specialists": selected_models,
            "report_synthesizer": synthesizer_model,
        },
        "specialist_outputs": specialist_results,
        "final_report_markdown": final_report,
    }
    return json.dumps(payload, indent=2)

def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Initialize session state if not present
        if "parallel_workers" not in st.session_state:
            st.session_state.parallel_workers = 2
        if "retry_attempts" not in st.session_state:
            st.session_state.retry_attempts = 3
        if "backoff_seconds" not in st.session_state:
            st.session_state.backoff_seconds = 3

        st.subheader("Presets")
        preset_col1, preset_col2 = st.columns(2)
        if preset_col1.button("🚀 Fast Mode", use_container_width=True):
            st.session_state.parallel_workers = 7
            st.session_state.retry_attempts = 1
            st.session_state.backoff_seconds = 1
            st.rerun()
        if preset_col2.button("🛡️ Reliable", use_container_width=True):
            st.session_state.parallel_workers = 3
            st.session_state.retry_attempts = 3
            st.session_state.backoff_seconds = 3
            st.rerun()
        
        st.divider()

        llm_provider = st.radio(
            "Primary LLM Provider",
            ["OpenRouter", "Groq"],
            index=0 if st.session_state.get("llm_provider", "OpenRouter") == "OpenRouter" else 1,
            help="Choose the primary provider for analysis."
        )
        st.session_state.llm_provider = llm_provider

        auto_pick_models = st.checkbox("Auto-pick models", value=True, help="Automatically select the best available free model for each task.")

        with st.expander("🛠️ Advanced Settings"):
            run_in_parallel = st.checkbox("Run in parallel", value=True)
            max_parallel_workers = st.slider(
                "Parallel workers",
                min_value=1,
                max_value=10,
                value=st.session_state.parallel_workers,
                key="parallel_workers_slider",
            )
            max_attempts_per_model = st.slider(
                "Retry attempts",
                min_value=1,
                max_value=5,
                value=st.session_state.retry_attempts,
                key="retry_attempts_slider",
            )
            base_backoff_seconds = st.slider(
                "Backoff (sec)",
                min_value=1,
                max_value=10,
                value=st.session_state.backoff_seconds,
                key="backoff_seconds_slider",
            )
            
            # Sync slider values back to session state if they were adjusted
            st.session_state.parallel_workers = max_parallel_workers
            st.session_state.retry_attempts = max_attempts_per_model
            st.session_state.backoff_seconds = base_backoff_seconds

        st.divider()
        st.caption("Architecture Guard v1.2")
        
        active_preset = "Custom"
        if (
            st.session_state.parallel_workers == 7
            and st.session_state.retry_attempts == 1
            and st.session_state.backoff_seconds == 1
        ):
            active_preset = "Fast"
        elif (
            st.session_state.parallel_workers == 3
            and st.session_state.retry_attempts == 3
            and st.session_state.backoff_seconds == 3
        ):
            active_preset = "Reliable"

        return {
            "llm_provider": llm_provider,
            "auto_pick_models": auto_pick_models,
            "run_in_parallel": run_in_parallel,
            "max_parallel_workers": max_parallel_workers,
            "max_attempts_per_model": max_attempts_per_model,
            "base_backoff_seconds": base_backoff_seconds,
            "active_preset": active_preset
        }

def render_export_downloads(final_report: str, run_id: str):
    """Renders download buttons for Docx and PDF."""
    col1, col2 = st.columns(2)
    
    # Word Export
    with col1:
        docx_path = f"/tmp/report_{run_id}.docx"
        try:
            export_to_docx(final_report, docx_path)
            with open(docx_path, "rb") as f:
                st.download_button(
                    label="📄 Download Word (.docx)",
                    data=f,
                    file_name=f"arch_review_{run_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Docx error: {e}")

    # PDF Export
    with col2:
        pdf_path = f"/tmp/report_{run_id}.pdf"
        try:
            export_to_pdf(final_report, pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📕 Download PDF (.pdf)",
                    data=f,
                    file_name=f"arch_review_{run_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"PDF error: {e}")
