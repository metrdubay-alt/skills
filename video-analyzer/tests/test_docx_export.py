import zipfile

from video_analyzer.docx_export import markdown_to_docx


def test_markdown_to_docx_writes_readable_word_document(tmp_path):
    markdown = """# Main Title

## Summary

Plain paragraph with **bold text** and `inline code`.

- First bullet
- Second bullet

1. First numbered
2. Second numbered

| Type | Name |
| --- | --- |
| metric | APR 12% |
"""
    output = tmp_path / "document.docx"

    markdown_to_docx(markdown, output)

    assert output.exists()
    with zipfile.ZipFile(output) as docx:
        xml = docx.read("word/document.xml").decode("utf-8")
    assert "Main Title" in xml
    assert "Summary" in xml
    assert "First bullet" in xml
    assert "Second numbered" in xml
    assert "APR 12%" in xml
