import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.utils.export import clean_for_pdf, export_to_docx, export_to_pdf

def test_clean_for_pdf():
    assert clean_for_pdf("**bold**") == "bold"
    assert clean_for_pdf("*italic*") == "italic"
    assert clean_for_pdf("`code`") == "code"
    # test character outside Latin-1
    assert clean_for_pdf("Hello\u2603") == "Hello "

@patch("src.utils.export.Document")
def test_export_to_docx(mock_document):
    mock_doc_instance = MagicMock()
    mock_document.return_value = mock_doc_instance

    markdown_content = "# Heading 1\n## Heading 2\n### Heading 3\n- Bullet 1\n* Bullet 2\n**Bold Text**"
    
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        temp_path = tf.name
        
    try:
        output_path = export_to_docx(markdown_content, temp_path)
        
        assert mock_document.called
        assert mock_doc_instance.add_heading.call_count >= 4 # Main title + 3 headings
        assert mock_doc_instance.add_paragraph.call_count >= 3 # 2 bullets + 1 line
        assert mock_doc_instance.save.called
        assert output_path == temp_path
    finally:
        os.remove(temp_path)

@patch("src.utils.export.FPDF")
def test_export_to_pdf(mock_fpdf):
    mock_pdf_instance = MagicMock()
    mock_fpdf.return_value = mock_pdf_instance

    markdown_content = "# Heading 1\n## Heading 2\n### Heading 3\nPlain Text\n\nEmpty line"
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        temp_path = tf.name
        
    try:
        output_path = export_to_pdf(markdown_content, temp_path)
        
        assert mock_fpdf.called
        assert mock_pdf_instance.add_page.called
        assert mock_pdf_instance.cell.called
        assert mock_pdf_instance.multi_cell.call_count >= 4
        assert mock_pdf_instance.output.called
        assert output_path == temp_path
    finally:
        os.remove(temp_path)
