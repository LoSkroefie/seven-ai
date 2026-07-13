import json
import zipfile

import pytest

from seven.tools.documents import document_status, read_document


def _zip(path, members):
    with zipfile.ZipFile(path, "w") as archive:
        for name, body in members.items():
            archive.writestr(name, body)


def test_text_json_csv_and_limits(tmp_path):
    text = tmp_path / "note.txt"
    text.write_text("Seven reads this locally", encoding="utf-8")
    assert "Seven reads this locally" in read_document(str(text))

    data = tmp_path / "data.json"
    data.write_text('{"name":"Seven"}', encoding="utf-8")
    assert '"name": "Seven"' in read_document(str(data))

    table = tmp_path / "table.csv"
    table.write_text('name,value\n"hello, world",7\n', encoding="utf-8")
    result = read_document(str(table))
    assert "hello, world | 7" in result
    assert '"rows": 2' in result

    long = tmp_path / "long.md"
    long.write_text("x" * 300, encoding="utf-8")
    assert '"truncated": true' in read_document(str(long), max_chars=100)


def test_docx_extraction(tmp_path):
    path = tmp_path / "sample.docx"
    _zip(path, {"word/document.xml": '<w:document xmlns:w="urn:w"><w:body><w:p><w:r><w:t>Hello Seven</w:t></w:r></w:p><w:p><w:r><w:t>Second paragraph</w:t></w:r></w:p></w:body></w:document>'})
    result = read_document(str(path))
    assert "Hello Seven\nSecond paragraph" in result
    assert '"blocks": 2' in result


def test_pptx_extraction_is_slide_ordered(tmp_path):
    path = tmp_path / "sample.pptx"
    _zip(path, {
        "ppt/slides/slide2.xml": '<p:sld xmlns:p="urn:p" xmlns:a="urn:a"><a:t>Second</a:t></p:sld>',
        "ppt/slides/slide1.xml": '<p:sld xmlns:p="urn:p" xmlns:a="urn:a"><a:t>First</a:t></p:sld>',
    })
    result = read_document(str(path))
    assert result.index("First") < result.index("Second")
    assert '"slides": 2' in result


def test_xlsx_shared_and_numeric_cells(tmp_path):
    path = tmp_path / "sample.xlsx"
    _zip(path, {
        "xl/sharedStrings.xml": '<sst xmlns="urn:x"><si><t>Name</t></si><si><t>Seven</t></si></sst>',
        "xl/worksheets/sheet1.xml": '<worksheet xmlns="urn:x"><sheetData><row><c t="s"><v>0</v></c><c t="s"><v>1</v></c><c><v>7</v></c></row></sheetData></worksheet>',
    })
    result = read_document(str(path))
    assert "Name | Seven | 7" in result
    assert '"sheets": 1' in result


def test_invalid_unsupported_and_optional_pdf_errors(tmp_path):
    bad = tmp_path / "bad.docx"
    bad.write_bytes(b"not a zip")
    assert read_document(str(bad)).startswith("ERROR reading")
    unknown = tmp_path / "thing.bin"
    unknown.write_bytes(b"data")
    assert "unsupported document type" in read_document(str(unknown))
    status = json.loads(document_status())
    assert status["office_backend"] == "stdlib OOXML"

    unsafe = tmp_path / "unsafe.docx"
    _zip(unsafe, {"../outside": "no", "word/document.xml": "<document/>"})
    assert "unsafe path" in read_document(str(unsafe))


def test_pdf_backend_reads_real_pdf(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    path = tmp_path / "sample.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as stream:
        writer.write(stream)
    result = read_document(str(path))
    assert '"pages": 1' in result
    assert "--- Page 1 ---" in result
