"""Bounded local extraction for text, data, PDF, and Office documents."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT_EXTENSIONS = {".txt", ".md", ".log", ".xml", ".html", ".htm", ".py", ".cs", ".js", ".ts", ".css", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".bat", ".ps1", ".sh"}
SUPPORTED = TEXT_EXTENSIONS | {".csv", ".json", ".pdf", ".docx", ".xlsx", ".pptx"}
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED = 200 * 1024 * 1024


def document_status() -> str:
    return json.dumps({
        "supported_extensions": sorted(SUPPORTED),
        "pdf_backend": "pypdf" if importlib.util.find_spec("pypdf") else None,
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


def register(reg):
    from seven.tools.registry import Tool
    reg.register(Tool("document_status", "Report supported local document formats and optional PDF backend.", {"type": "object", "properties": {}}, document_status))
    reg.register(Tool("read_document", "Extract bounded local text from PDF, DOCX, XLSX, PPTX, CSV, JSON, and text documents.", {
        "type": "object", "properties": {
            "path": {"type": "string"},
            "max_chars": {"type": "integer", "minimum": 100, "maximum": 200000},
        }, "required": ["path"]}, read_document))
