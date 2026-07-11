# Structured document reading

Seven's `read_document` tool extracts local text from `.txt`, `.md`, common source/configuration formats, `.csv`, `.json`, `.docx`, `.xlsx`, `.pptx`, and `.pdf`. `document_status` reports the exact runtime support and limits.

DOCX, XLSX, and PPTX are parsed locally using Python's standard ZIP/XML libraries. PDF extraction is available through the `documents` extra:

```bash
pip install "seven-ai[documents]"
```

No document is uploaded and extraction does not invoke an LLM. After extraction, Seven's configured brain can reason over the returned bounded text in the ordinary conversation/tool loop.

## Bounds and truthful behavior

- Input files are capped at 50 MiB.
- Expanded Office archives are capped at 200 MiB and unsafe member paths are rejected.
- Returned text is capped between 100 and 200,000 characters; metadata says whether truncation occurred and reports the untruncated character count.
- PDF results report actual pages reached by `pypdf`. Image-only/scanned PDFs can legitimately contain little or no text; OCR is not claimed.
- XLSX output contains cell values, not formula recalculation, charts, macros, styling, comments, or hidden-object interpretation.
- DOCX/PPTX output contains visible XML text in document/slide order, not a layout-faithful rendering.
- Encrypted, malformed, unsupported, or dependency-missing files return explicit errors.

This is unrestricted local host access consistent with Seven's L4 model. The calling user/client must already have filesystem permission to the path.

## Legacy disposition

The v3 reader claimed “PDFs and Documents” but actually supported PDF plus generic text/CSV/JSON; it did not implement DOCX despite its title and depended on an undeclared `PyPDF2` installation. Its Ollama summarizer silently fell back to raw text. The current tool separates deterministic extraction from model reasoning, declares the PDF dependency, and adds directly tested Office formats and resource limits.
