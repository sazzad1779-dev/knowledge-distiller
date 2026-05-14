# Node 2: Section Splitter

The Splitter node intelligently breaks down the massive raw text into manageable sections (usually chapters or sub-chapters) for processing.

## Splitting Strategies

The system tries strategies in the following order of priority:

1. **Heading-based (Markdown/EPUB)**: Uses H1-H3 tags or chapter boundaries.
2. **PDF Font Detection**: Detects headings based on bold styles and larger font sizes (provided by PyMuPDF).
3. **Keyword Matching**: Scans for patterns like "Chapter N", "Section N", or "Part N".
4. **Fallback (Page-chunking)**: If no structure is detected, it splits every *N* pages (default: 10).

## Configuration

```yaml
splitter:
  min_section_words: 200    # Merge tiny sections with the next one
  max_section_words: 8000   # Split very large sections at paragraph boundaries
  fallback_page_chunk: 10   # Chunk size for unstructured documents
```

## Section Object

Each section contains:
- `index`: Sequential order.
- `title`: Extracted or auto-generated heading.
- `text`: The raw content.
- `page_start` / `page_end`: Bounds in the original document.
- `has_images`: Flag indicating if images are present in this range.
