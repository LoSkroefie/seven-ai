"""Bounded local extraction for text, data, PDF, and Office documents."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import textwrap
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT_EXTENSIONS = {".txt", ".md", ".log", ".xml", ".html", ".htm", ".py", ".cs", ".js", ".ts", ".css", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".bat", ".ps1", ".sh"}
SUPPORTED = TEXT_EXTENSIONS | {".csv", ".json", ".pdf", ".docx", ".xlsx", ".pptx"}
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED = 200 * 1024 * 1024
MAX_PDF_TEXT = 200_000


def document_status() -> str:
    return json.dumps({
        "supported_extensions": sorted(SUPPORTED),
        "pdf_backend": "pypdf" if importlib.util.find_spec("pypdf") else None,
        "pdf_write_backend": "reportlab" if importlib.util.find_spec("reportlab") else None,
        "office_backend": "stdlib OOXML",
        "max_file_bytes": MAX_FILE_BYTES,
        "max_archive_uncompressed_bytes": MAX_ARCHIVE_UNCOMPRESSED,
    }, indent=2)


def _bounded(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n...[truncated]", True


def _safe_archive(path: Path) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(path)
    total = sum(info.file_size for info in archive.infolist())
    if total > MAX_ARCHIVE_UNCOMPRESSED:
        archive.close()
        raise ValueError(f"expanded archive exceeds {MAX_ARCHIVE_UNCOMPRESSED} bytes")
    if any(info.filename.startswith(("/", "\\")) or ".." in Path(info.filename).parts for info in archive.infolist()):
        archive.close()
        raise ValueError("unsafe path in Office archive")
    return archive


def _xml_text(blob: bytes) -> str:
    root = ET.fromstring(blob)
    return " ".join((node.text or "").strip() for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "t" and (node.text or "").strip())


def _read_docx(path: Path) -> tuple[str, dict]:
    with _safe_archive(path) as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("invalid DOCX: word/document.xml missing")
        root = ET.fromstring(archive.read("word/document.xml"))
        blocks = []
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] == "p":
                text = " ".join((child.text or "").strip() for child in node.iter() if child.tag.rsplit("}", 1)[-1] == "t" and (child.text or "").strip())
                if text:
                    blocks.append(text)
        return "\n".join(blocks), {"blocks": len(blocks)}


def _read_pptx(path: Path) -> tuple[str, dict]:
    with _safe_archive(path) as archive:
        slides = sorted(n for n in archive.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
        if not slides:
            raise ValueError("invalid PPTX: no slides found")
        parts = [f"--- Slide {index} ---\n{_xml_text(archive.read(name))}" for index, name in enumerate(slides, 1)]
        return "\n\n".join(parts), {"slides": len(slides)}


def _read_xlsx(path: Path) -> tuple[str, dict]:
    with _safe_archive(path) as archive:
        names = archive.namelist()
        sheets = sorted(n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        if not sheets:
            raise ValueError("invalid XLSX: no worksheets found")
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root:
                shared.append(" ".join((n.text or "") for n in item.iter() if n.tag.rsplit("}", 1)[-1] == "t"))
        output, row_count = [], 0
        for sheet_index, name in enumerate(sheets, 1):
            output.append(f"--- Sheet {sheet_index} ---")
            root = ET.fromstring(archive.read(name))
            for row in (n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "row"):
                values = []
                for cell in (n for n in row if n.tag.rsplit("}", 1)[-1] == "c"):
                    kind = cell.attrib.get("t")
                    value_node = next((n for n in cell if n.tag.rsplit("}", 1)[-1] in {"v", "is"}), None)
                    raw = "" if value_node is None else (value_node.text or _xml_text(ET.tostring(value_node)))
                    if kind == "s" and raw.isdigit() and int(raw) < len(shared):
                        raw = shared[int(raw)]
                    values.append(raw)
                output.append(" | ".join(values))
                row_count += 1
        return "\n".join(output), {"sheets": len(sheets), "rows": row_count}


def read_document(path: str, max_chars: int = 50_000) -> str:
    p = Path(path).expanduser().resolve()
    max_chars = max(100, min(int(max_chars), 200_000))
    if not p.exists() or not p.is_file():
        return f"ERROR: file not found: {p}"
    size = p.stat().st_size
    if size > MAX_FILE_BYTES:
        return f"ERROR: file is {size} bytes; limit is {MAX_FILE_BYTES}"
    ext = p.suffix.lower()
    if ext not in SUPPORTED:
        return f"ERROR: unsupported document type '{ext or '(none)'}'"
    try:
        meta = {}
        if ext in TEXT_EXTENSIONS:
            text = p.read_text(encoding="utf-8", errors="replace")
        elif ext == ".json":
            text = json.dumps(json.loads(p.read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
        elif ext == ".csv":
            rows = list(csv.reader(io.StringIO(p.read_text(encoding="utf-8-sig", errors="replace"))))
            text, meta = "\n".join(" | ".join(row) for row in rows), {"rows": len(rows)}
        elif ext == ".docx":
            text, meta = _read_docx(p)
        elif ext == ".pptx":
            text, meta = _read_pptx(p)
        elif ext == ".xlsx":
            text, meta = _read_xlsx(p)
        else:
            try:
                from pypdf import PdfReader
            except ImportError:
                return "ERROR: PDF support requires: pip install 'seven-ai[documents]'"
            reader = PdfReader(str(p))
            parts = [f"--- Page {i} ---\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages, 1)]
            text, meta = "\n\n".join(parts), {"pages": len(reader.pages)}
        total_chars = len(text)
        text, truncated = _bounded(text, max_chars)
        header = {"path": str(p), "type": ext.lstrip("."), "bytes": size, "total_chars": total_chars, "truncated": truncated, **meta}
        return json.dumps(header, ensure_ascii=False) + "\n\n" + text
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        return f"ERROR reading {p}: {exc}"


def write_pdf(path: str, title: str, content: str) -> str:
    """Create a bounded local text PDF with atomic replacement."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from reportlab.pdfgen import canvas
    except ImportError:
        return "ERROR: PDF creation requires: pip install 'seven-ai[documents]'"

    title = str(title or "").strip()
    content = str(content or "")
    if not title or len(title) > 500:
        return "ERROR: title must contain 1-500 characters"
    if len(content) > MAX_PDF_TEXT:
        return f"ERROR: PDF content exceeds {MAX_PDF_TEXT} characters"
    destination = Path(path).expanduser().resolve()
    if destination.suffix.lower() != ".pdf":
        return "ERROR: PDF destination must end with .pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".seven-pdf-", suffix=".tmp", dir=str(destination.parent)
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        page_width, page_height = A4
        document = canvas.Canvas(str(temporary), pagesize=A4)
        left = 54
        right = 54
        top = 54
        bottom = 54
        usable = page_width - left - right

        def draw_wrapped(text: str, font: str, size: int, leading: int, y: float) -> float:
            document.setFont(font, size)
            for paragraph in str(text).splitlines() or [""]:
                words = paragraph.expandtabs(4).split(" ")
                line = ""
                wrapped = []
                for word in words:
                    candidate = word if not line else f"{line} {word}"
                    if stringWidth(candidate, font, size) <= usable:
                        line = candidate
                    else:
                        if line:
                            wrapped.append(line)
                        if stringWidth(word, font, size) <= usable:
                            line = word
                        else:
                            approx = max(1, int(usable / max(size * 0.55, 1)))
                            pieces = textwrap.wrap(
                                word,
                                width=approx,
                                break_long_words=True,
                                break_on_hyphens=False,
                            )
                            wrapped.extend(pieces[:-1])
                            line = pieces[-1] if pieces else ""
                wrapped.append(line)
                for item in wrapped:
                    if y < bottom:
                        document.showPage()
                        document.setFont(font, size)
                        y = page_height - top
                    document.drawString(left, y, item)
                    y -= leading
            return y

        y_position = draw_wrapped(title, "Helvetica-Bold", 18, 24, page_height - top)
        y_position -= 10
        draw_wrapped(content, "Helvetica", 10, 14, y_position)
        document.save()
        size = temporary.stat().st_size
        if size <= 0:
            return "ERROR: PDF backend produced an empty file"
        os.replace(temporary, destination)
        return json.dumps(
            {
                "ok": True,
                "path": str(destination),
                "bytes": size,
                "title": title,
            }
        )
    except (OSError, ValueError) as exc:
        return f"ERROR writing PDF: {exc}"
    finally:
        temporary.unlink(missing_ok=True)


def register(reg):
    from seven.tools.registry import Tool
    reg.register(Tool("document_status", "Report supported local document formats and optional PDF read/write backends.", {"type": "object", "properties": {}}, document_status))
    reg.register(Tool("read_document", "Extract bounded local text from PDF, DOCX, XLSX, PPTX, CSV, JSON, and text documents.", {
        "type": "object", "properties": {
            "path": {"type": "string"},
            "max_chars": {"type": "integer", "minimum": 100, "maximum": 200000},
        }, "required": ["path"]}, read_document))
    reg.register(Tool("write_pdf", "Create a bounded local text PDF with atomic replacement.", {
        "type": "object", "properties": {
            "path": {"type": "string"},
            "title": {"type": "string"},
            "content": {"type": "string"},
        }, "required": ["path", "title", "content"]}, write_pdf))
