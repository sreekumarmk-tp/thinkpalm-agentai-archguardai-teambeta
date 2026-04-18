import pytest
from unittest.mock import patch, call
from src.utils.rendering import render_mermaid, display_enriched_report

@patch('src.utils.rendering.components.html')
@patch('builtins.open')
@patch('os.path.exists')
def test_render_mermaid_with_local_js(mock_exists, mock_open, mock_html):
    mock_exists.return_value = True
    mock_open.return_value.__enter__.return_value.read.return_value = "console.log('mermaid');"
    
    render_mermaid("graph TD;\nA-->B;", "test-key")
    
    mock_html.assert_called_once()
    html_arg = mock_html.call_args[0][0]
    assert "console.log('mermaid');" in html_arg
    assert "graph TD;" in html_arg

@patch('src.utils.rendering.components.html')
@patch('os.path.exists')
def test_render_mermaid_without_local_js(mock_exists, mock_html):
    mock_exists.return_value = False
    
    render_mermaid("graph TD;\nA-->B;", "test-key-2")
    
    mock_html.assert_called_once()
    html_arg = mock_html.call_args[0][0]
    assert "cdn.jsdelivr.net" in html_arg
    assert "graph TD;" in html_arg


@patch('src.utils.rendering.render_mermaid')
@patch('src.utils.rendering.st.markdown')
def test_display_enriched_report(mock_markdown, mock_render_mermaid):
    report_text = """
# Header
Some text here.
```mermaid
graph TD;
A-->B;
```
More text.
"""
    display_enriched_report(report_text)
    
    # Check that markdown was called for the text parts
    assert mock_markdown.call_count >= 2
    
    # Check that render_mermaid was called for the mermaid block
    mock_render_mermaid.assert_called_once_with("graph TD;\nA-->B;", key="diag-1")
