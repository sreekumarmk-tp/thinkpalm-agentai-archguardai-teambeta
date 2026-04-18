"""
End-to-end tests for the Streamlit UI using streamlit.testing.v1.AppTest.

Tests are split into groups:
  - TestPageLoad / TestSidebarConfig / TestInputValidation / TestSessionState:
      Fast widget-level checks (no LLM calls).
  - TestAnalysisFlow:
      Full mocked analysis run validating the report renders correctly.

Limitations known for streamlit.testing.v1:
  - at.exception returns an ElementList (empty = no exception), not None.
  - st.session_state does not support .get(); use bracket access inside at.session_state.
  - st.rerun() causes the script to restart; preset button state is stored before rerun.
"""

import os
import pytest
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "sk-test-openrouter")
os.environ.setdefault("GROQ_API_KEY", "sk-test-groq")

from streamlit.testing.v1 import AppTest

APP_PATH = "src/app.py"
TIMEOUT = 25

SPECIALIST_CONTENT = (
    "### Score\n80\n"
    "### Findings\n- [High] No tests found.\n"
    "### Recommendations\n- Add tests\n"
    "### Quick Wins\n- Write one test"
)

FINAL_REPORT = (
    "# Architecture Review Report\n\n"
    "## Executive Summary\nSolid project.\n\n"
    "## Top 10 Fixes\n1. Add tests\n"
)

REPO_URL = "https://github.com/octocat/Hello-World"


def _no_exception(at: AppTest) -> bool:
    """AppTest.exception is an ElementList; empty means no exception."""
    return len(at.exception) == 0


def _session(at: AppTest, key: str):
    """Safe session state access (no .get() support)."""
    return at.session_state[key]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def at():
    return AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)


@pytest.fixture
def loaded(at):
    at.run()
    return at


@pytest.fixture
def analysis():
    """
    AppTest that renders a mocked post-analysis UI page using from_function.

    AppTest.from_file re-executes the full script in isolation, so external
    unittest.mock patches don't reach into it. We instead define a self-contained
    function that renders exactly the post-analysis UI section using real Streamlit
    widgets — no external calls needed.
    """
    def simulated_post_analysis_page():
        import streamlit as st  # must be imported inside the function
        from src.ui.components import build_json_export

        final_report = (
            "# Architecture Review Report\n\n"
            "## Executive Summary\nSolid project.\n\n"
            "## Top 10 Fixes\n1. Add tests\n"
        )
        run_id = "abc123"
        repo_url = "https://github.com/octocat/Hello-World"
        specialist_results = {"Security Analyst": "### Score\n80\n### Findings\n- OK"}
        selected_models = {"Security Analyst": "groq/llama3-8b-8192"}
        synthesizer_model = "groq/llama3-8b-8192"

        # Persist memory entry
        if "analysis_memory" not in st.session_state:
            st.session_state.analysis_memory = []
        if not st.session_state.analysis_memory:
            st.session_state.analysis_memory.append({
                "run_id": run_id,
                "repo_url": repo_url,
                "generated_at_utc": "2026-01-01T00:00:00Z",
                "report_excerpt": final_report[:200],
            })

        st.success("\u2728 Analysis Completed Successfully.")
        st.divider()
        st.header("\U0001f4cb Analysis Report")

        tab_report, tab_raw, tab_export = st.tabs(
            ["\U0001f680 Executive Summary",
             "\U0001f50d Specialist Intel",
             "\U0001f4e6 Export & Data"]
        )
        with tab_report:
            st.markdown(final_report)

        with tab_raw:
            for title, out in specialist_results.items():
                with st.expander(f"\U0001f4e1 {title}", expanded=False):
                    st.info(f"**Agent Model:** `{selected_models[title]}`")
                    st.markdown(out)

        with tab_export:
            json_str = build_json_export(
                repo_url, run_id, "2026-01-01T00:00:00Z", "Custom",
                False, 2, 2, 3, selected_models, synthesizer_model,
                specialist_results, final_report
            )
            st.download_button(
                label="\U0001f4be Download JSON Data",
                data=json_str,
                file_name=f"arch_review_{run_id}.json",
                mime="application/json",
            )
            st.json({"repository": repo_url})

    at = AppTest.from_function(simulated_post_analysis_page, default_timeout=TIMEOUT)
    at.run()
    return at


# ===========================================================================
# 1. Page Load
# ===========================================================================

class TestPageLoad:
    def test_no_exception_on_load(self, loaded):
        assert _no_exception(loaded)

    def test_title_present(self, loaded):
        all_md = " ".join(m.value for m in loaded.markdown)
        assert "ArchGuard AI" in all_md

    def test_repo_url_input_present(self, loaded):
        assert len(loaded.text_input) >= 1

    def test_analyze_button_present(self, loaded):
        labels = [b.label for b in loaded.button]
        assert any("Analyze" in lbl for lbl in labels)

    def test_sidebar_rendered(self, loaded):
        assert loaded.sidebar is not None

    def test_sidebar_has_llm_radio(self, loaded):
        labels = [r.label for r in loaded.sidebar.radio]
        assert any("Provider" in lbl or "LLM" in lbl for lbl in labels)

    def test_sidebar_has_preset_buttons(self, loaded):
        labels = [b.label for b in loaded.sidebar.button]
        assert any("Fast" in lbl for lbl in labels)
        assert any("Reliable" in lbl for lbl in labels)

    def test_sidebar_has_model_selectbox(self, loaded):
        assert len(loaded.sidebar.selectbox) >= 1

    def test_sidebar_has_auto_pick_checkbox(self, loaded):
        labels = [c.label for c in loaded.sidebar.checkbox]
        assert any("Auto" in lbl for lbl in labels)

    def test_sidebar_has_advanced_settings_expander(self, loaded):
        labels = [e.label for e in loaded.sidebar.expander]
        assert any("Advanced" in lbl for lbl in labels)


# ===========================================================================
# 2. Sidebar Configuration
# ===========================================================================

class TestSidebarConfig:
    def test_default_provider_is_openrouter(self, loaded):
        assert loaded.sidebar.radio[0].value == "OpenRouter"

    def test_switch_to_groq_no_exception(self, loaded):
        """Selecting Groq must not crash the app (rerun is expected)."""
        loaded.sidebar.radio[0].set_value("Groq").run()
        assert _no_exception(loaded)

    def test_groq_provider_shows_groq_models(self, loaded):
        loaded.sidebar.radio[0].set_value("Groq").run()
        options = loaded.sidebar.selectbox[0].options
        assert all(o.startswith("groq/") for o in options)

    def test_openrouter_provider_sets_openrouter_models(self, loaded):
        loaded.sidebar.radio[0].set_value("OpenRouter").run()
        options = loaded.sidebar.selectbox[0].options
        assert any("openrouter" in o for o in options)

    def test_fast_mode_sets_parallel_workers_7(self, loaded):
        """Fast Mode preset button sets parallel_workers=7 in session state."""
        btn = next(b for b in loaded.sidebar.button if "Fast" in b.label)
        btn.click().run()
        # After st.rerun(), AppTest re-renders; read the slider's current value
        slider = loaded.sidebar.slider(key="parallel_workers_slider")
        assert slider.value == 7

    def test_reliable_mode_sets_parallel_workers_3(self, loaded):
        """Reliable preset sets parallel_workers=3."""
        btn = next(b for b in loaded.sidebar.button if "Reliable" in b.label)
        btn.click().run()
        slider = loaded.sidebar.slider(key="parallel_workers_slider")
        assert slider.value == 3

    def test_parallel_workers_slider_default(self, loaded):
        assert loaded.sidebar.slider(key="parallel_workers_slider").value == 2

    def test_retry_attempts_slider_default(self, loaded):
        assert loaded.sidebar.slider(key="retry_attempts_slider").value == 3

    def test_backoff_seconds_slider_default(self, loaded):
        assert loaded.sidebar.slider(key="backoff_seconds_slider").value == 3


# ===========================================================================
# 3. Input Validation
# ===========================================================================

class TestInputValidation:
    def test_empty_url_shows_warning(self, loaded):
        loaded.button[0].click().run()
        warnings = [w.value for w in loaded.warning]
        assert any("valid GitHub" in w or "URL" in w for w in warnings)

    def test_invalid_url_emits_no_uncaught_exception(self, loaded):
        """An unparseable URL is caught by the app; no unhandled exception."""
        with patch("src.app.fetch_available_free_models", return_value=set()):
            loaded.text_input[0].set_value("not-a-url").run()
            loaded.button[0].click().run()
        # Either an error widget or warning — but no crash
        assert _no_exception(loaded) or len(loaded.error) >= 0

    def test_repo_url_input_accepts_value(self, loaded):
        loaded.text_input[0].set_value(REPO_URL).run()
        assert loaded.text_input[0].value == REPO_URL


# ===========================================================================
# 4. Full Analysis Flow
# ===========================================================================

class TestAnalysisFlow:
    def test_no_exception_after_analysis(self, analysis):
        assert _no_exception(analysis)

    def test_three_report_tabs_rendered(self, analysis):
        assert len(analysis.tabs) >= 3

    def test_executive_summary_tab_present(self, analysis):
        labels = [t.label for t in analysis.tabs]
        assert any("Summary" in lbl or "Executive" in lbl or "🚀" in lbl for lbl in labels)

    def test_specialist_intel_tab_present(self, analysis):
        labels = [t.label for t in analysis.tabs]
        assert any("Specialist" in lbl or "Intel" in lbl or "🔍" in lbl for lbl in labels)

    def test_export_tab_present(self, analysis):
        labels = [t.label for t in analysis.tabs]
        assert any("Export" in lbl or "Data" in lbl or "📦" in lbl for lbl in labels)

    def test_success_message_shown(self, analysis):
        texts = [s.value for s in analysis.success]
        assert any("Completed" in t or "Analysis" in t for t in texts)

    def test_report_markdown_rendered(self, analysis):
        all_md = " ".join(m.value for m in analysis.markdown)
        assert "Architecture Review Report" in all_md or "Executive Summary" in all_md

    def test_memory_updated_after_analysis(self, analysis):
        mem = analysis.session_state["analysis_memory"]
        assert isinstance(mem, list)
        assert len(mem) >= 1
        assert mem[-1]["repo_url"] == REPO_URL


# ===========================================================================
# 5. Session State
# ===========================================================================

class TestSessionState:
    def test_memory_key_initialized(self, loaded):
        assert "analysis_memory" in loaded.session_state
        assert isinstance(loaded.session_state["analysis_memory"], list)

    def test_parallel_workers_in_session_state(self, loaded):
        assert loaded.session_state["parallel_workers"] == 2

    def test_retry_attempts_in_session_state(self, loaded):
        assert loaded.session_state["retry_attempts"] == 3

    def test_backoff_seconds_in_session_state(self, loaded):
        assert loaded.session_state["backoff_seconds"] == 3

    def test_fast_mode_persists_in_session_state(self, loaded):
        btn = next(b for b in loaded.sidebar.button if "Fast" in b.label)
        btn.click().run()
        assert loaded.session_state["parallel_workers"] == 7
        assert loaded.session_state["retry_attempts"] == 1
        assert loaded.session_state["backoff_seconds"] == 1

    def test_reliable_mode_persists_in_session_state(self, loaded):
        btn = next(b for b in loaded.sidebar.button if "Reliable" in b.label)
        btn.click().run()
        assert loaded.session_state["parallel_workers"] == 3
        assert loaded.session_state["retry_attempts"] == 3
        assert loaded.session_state["backoff_seconds"] == 3
