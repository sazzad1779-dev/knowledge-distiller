# Node 1: Document Loader

The Loader node is responsible for ingesting various file formats and converting them into a unified internal representation.

## Supported Formats

| Extension | Library | Capabilities |
|---|---|---|
| `.pdf` | `PyMuPDF (fitz)` | Text extraction, page mapping, image extraction metadata |
| `.epub` | `ebooklib` | Structured chapter loading, HTML-to-text conversion |
| `.docx` | `python-docx` | Paragraph and heading extraction |
| `.txt` / `.md` | Built-in | Plain text reading |

## Responsibilities
- **Type Detection**: Auto-detects file type based on extension.
- **Metadata Extraction**: Captures document title, author, and total page count.
- **Unified Output**: Produces a `DocumentState` object containing the full raw text and a list of `PageData` (page number + text).

## Internal Schema

```python
class DocumentState(TypedDict):
    file_path: str
    file_type: str         # "pdf" | "epub" | "docx" | "txt"
    raw_text: str
    metadata: dict         # title, author, pages
    pages: list[PageData]  # [{page_num, text, has_images}]
```
