# Node 5: Output Writer

The Writer node handles the persistent storage of distilled knowledge, ensuring progress is saved incrementally.

## Incremental Appending
Unlike standard converters that write the entire file at the end, the Knowledge Distiller appends to the Markdown file **section-by-section**.
- **Benefit**: If the pipeline crashes (e.g., API outage or power loss) at Section 50, Sections 1–49 are already safely written to disk.

## Output Format: Markdown
The final output is a single `.md` file with the following structure:

1. **Document Header**: YAML-like metadata (Title, Source, Timestamp, LLM used).
2. **Section Headings**: Derived from the Splitter node.
3. **Distilled Content**: The AI-generated concept list.
4. **Images**: Inserted at the end of their respective sections using relative Markdown links.
5. **Horizontal Rules**: Clear separation between chapters/sections.

## Directory Structure
```text
/output
  ├── my_book_distilled.md
  └── /images
      └── /my_book
          ├── 0_1.png
          ├── 1_1.png
          └── ...
```
