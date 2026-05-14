# Knowledge Distiller Documentation

Welcome to the technical documentation for the Knowledge Distiller project.

## Core Pipeline
- [Pipeline Architecture](pipeline.md) — Overview of the LangGraph flow and state management.

## Pipeline Nodes
1. [Node 1: Document Loader](loader.md) — Handling PDF, EPUB, DOCX, and TXT files.
2. [Node 2: Section Splitter](splitter.md) — Logic for breaking documents into chapters.
3. [Node 3: Image Extractor](image_extractor.md) — Extracting and filtering visual assets.
4. [Node 4: AI Distiller](distiller.md) — The core AI logic and prompting strategy.
5. [Node 5: Output Writer](writer.md) — Incremental Markdown file generation.

## Implementation Details
For the detailed roadmap of building this system, please refer to the [Implementation Plan](../implementation_plan.md) (internal artifact).
