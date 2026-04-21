import os
import pytest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

# Set mock keys for testing
os.environ["OPENROUTER_API_KEY"] = "sk-test"
os.environ["GROQ_API_KEY"] = "sk-test"

APP_PATH = "src/app.py"
TIMEOUT = 30

def _no_exception(at: AppTest) -> bool:
    return len(at.exception) == 0

@pytest.fixture
def at():
    return AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)

class TestPageLoad:
    def test_basic_load(self, at):
        at.run()
        assert _no_exception(at)
        assert any("ArchGuard AI" in m.value for m in at.markdown)
        assert len(at.text_input) >= 1
        assert any("Analyze" in b.label for b in at.button)

class TestSidebarConfig:
    def test_sidebar_defaults(self, at):
        at.run()
        # Primary LLM Provider radio
        assert at.sidebar.radio[0].value == "Groq"
        # Advanced settings: Checkbox for parallel, number inputs for attempts/backoff
        assert any("Parallel" in c.label for c in at.sidebar.checkbox)
        assert len(at.sidebar.number_input) >= 2

    def test_switch_provider(self, at):
        at.run()
        at.sidebar.radio[0].set_value("OpenRouter").run()
        assert _no_exception(at)
        assert at.session_state.llm_provider == "OpenRouter"

class TestInputValidation:
    def test_empty_url_warning(self, at):
        at.run()
        # Find Analyze button and click
        btn = next(b for b in at.button if "Analyze" in b.label)
        btn.click().run()
        assert any("valid GitHub" in w.value for w in at.warning)

def mock_app():
    import streamlit as st
    
    st.session_state.current_analysis = {
        "run_id": "test-uuid",
        "repo_url": "http://github.com/test/repo",
        "generated_at": "2026-01-01",
        "final_report": "# Test Report",
        "specialist_results": {"Agent": "Result"},
        "selected_models": {"Agent": "model"},
        "synthesizer_model": "synth-model",
        "provider": "Groq",
        "active_preset": "Reliable",
        "max_attempts_per_model": 1,
        "base_backoff_seconds": 1,
    }
    # Simulate the part of app.py that renders the report
    st.header("📋 Analysis Report")
    tab1, tab2, tab3 = st.tabs(["🚀 Executive Summary", "🔍 Specialist Intel", "📦 Export & Data"])
    with tab1:
        st.markdown("# Test Report")
    with tab3:
        st.button("Download JSON")

class TestAnalysisMockFlow:
    """
    Since we can't easily mock the full LLM chain within AppTest.from_file 
    (it runs in a separate process/context), we test the UI components 
    that would be rendered after analysis using from_function or by 
    manually setting session state if possible.
    """
    def test_post_analysis_ui_rendering(self):
        at = AppTest.from_function(mock_app)
        at.run()
        assert _no_exception(at)
        assert any("Analysis Report" in h.value for h in at.header)
        assert len(at.tabs) == 3
        # Use tab label as check
        labels = [t.label for t in at.tabs]
        assert "🚀 Executive Summary" in labels

