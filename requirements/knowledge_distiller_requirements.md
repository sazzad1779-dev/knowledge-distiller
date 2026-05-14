# Knowledge Distiller — System Requirements

> **Purpose:** An AI-powered pipeline that takes technical/academic books or documents,
> splits them by topic, distills each section into compact, clear knowledge with examples,
> and appends the output into a structured Markdown file — removing noise without losing concepts.

---

## 1. Project Overview

### Problem
Technical and academic books are dense, repetitive, and padded. Reading them cover-to-cover
wastes time on re-explanations, motivating stories, and filler content. Existing summarizers
lose important concepts. This system solves that by **distilling** — keeping every concept,
removing all noise, and adding clarity through examples.

### Goal
Build a LangGraph pipeline that:
1. Accepts a document (PDF, EPUB, TXT, DOCX)
2. Splits it intelligently by heading/topic/section
3. Processes each section through a custom AI distillation prompt
4. Copies over any images/diagrams found in the section
5. Appends the distilled output to a single structured `.md` file

---

## 2. Tech Stack

| Component       | Choice                          | Notes                                   |
|-----------------|---------------------------------|-----------------------------------------|
| Pipeline        | **LangGraph**                   | Each step = a node; supports conditional edges |
| LLM Providers   | **Google Gemini** + **OpenAI**  | Configurable per node; fallback support |
| Document Parsing| `PyMuPDF (fitz)`, `ebooklib`, `python-docx` | For PDF, EPUB, DOCX respectively |
| Image Extraction| `PyMuPDF`, `Pillow`             | Extract and save embedded images/diagrams |
| Output Format   | **Markdown (`.md`)**            | Appended section-by-section             |
| Config          | `pydantic-settings` + `.env`    | API keys, model selection, prompt config |
| Package Manager | `uv` or `pip`                   | Python 3.11+                            |

---

## 3. System Architecture — LangGraph Pipeline

```
[START]
   │
   ▼
┌─────────────────────┐
│  Node 1: LOAD       │  ← Accept file path or URL
│  Document Loader    │    Detect file type (PDF/EPUB/DOCX/TXT)
└────────┬────────────┘    Return raw document object
         │
         ▼
┌─────────────────────┐
│  Node 2: SPLIT      │  ← Split by: Heading (H1/H2), Chapter markers,
│  Section Splitter   │    or page-based fallback if no headings found
└────────┬────────────┘    Output: List of sections [{title, text, page_range}]
         │
         ▼
┌─────────────────────┐
│  Node 3: EXTRACT    │  ← For each section:
│  Image Extractor    │    Find embedded images/diagrams by page range
└────────┬────────────┘    Save to /output/images/{section_slug}_{n}.png
         │
         ▼
┌─────────────────────┐
│  Node 4: DISTILL    │  ← For each section (one by one):
│  AI Distillation    │    Send text to LLM with custom prompt
└────────┬────────────┘    Get back structured distilled content
         │
         ▼
┌─────────────────────┐
│  Node 5: APPEND     │  ← Format distilled content as Markdown
│  Output Writer      │    Append to output .md file
└────────┬────────────┘    Include image references inline
         │
         ▼
┌─────────────────────┐
│  Node 6: VALIDATE   │  ← Check no concepts were lost (optional LLM check)
│  Quality Check      │    Flag sections that seem too short vs input length
└────────┬────────────┘
         │
         ▼
       [END]
```

---

## 4. Node Specifications

### Node 1 — Document Loader

**Input:** File path (string)
**Output:** `DocumentState` object

**Responsibilities:**
- Detect file type from extension
- Load file using appropriate parser:
  - `.pdf` → PyMuPDF (`fitz`)
  - `.epub` → `ebooklib`
  - `.docx` → `python-docx`
  - `.txt` / `.md` → plain read
- Extract full text with page numbers preserved
- Extract document metadata (title, author, total pages)

**Output Schema:**
```python
class DocumentState(TypedDict):
    file_path: str
    file_type: str         # "pdf" | "epub" | "docx" | "txt"
    raw_text: str
    metadata: dict         # title, author, pages
    pages: list[PageData]  # [{page_num, text, has_images}]
```

---

### Node 2 — Section Splitter

**Input:** `DocumentState`
**Output:** `List[Section]`

**Splitting Strategy (in priority order):**

| Priority | Method                        | When Used                                    |
|----------|-------------------------------|----------------------------------------------|
| 1        | Markdown/EPUB headings (H1-H3)| EPUB files, Markdown files                   |
| 2        | PDF heading detection         | Bold + large font size text in PDF           |
| 3        | Chapter keyword matching      | "Chapter N", "Section N", "Part N" patterns  |
| 4        | Fixed page-count chunking     | Fallback — every N pages (default: 10)       |

**Output Schema:**
```python
class Section(TypedDict):
    index: int
    title: str             # Extracted or generated heading
    text: str              # Full raw text of the section
    page_start: int
    page_end: int
    word_count: int
    has_images: bool       # Whether images exist in this page range
```

**Config Options:**
```yaml
splitter:
  min_section_words: 200    # Merge tiny sections with the next one
  max_section_words: 8000   # Split very large sections at paragraph boundary
  fallback_page_chunk: 10   # Pages per chunk when no headings found
```

---

### Node 3 — Image Extractor

**Input:** `List[Section]`, original file
**Output:** `List[Section]` (updated with image paths)

**Responsibilities:**
- For each section, scan its page range for embedded images/figures
- Skip decorative images (very small, header/footer logos) based on size threshold
- Save extracted images to: `./output/images/{document_slug}/{section_index}_{n}.png`
- Update section with list of image file paths

**Config Options:**
```yaml
image_extractor:
  min_image_width: 100      # px — ignore images smaller than this
  min_image_height: 100     # px — ignore images smaller than this
  output_dir: "./output/images"
  skip_if_no_images: true   # Skip node entirely if doc has no images
```

---

### Node 4 — AI Distillation (Core Node)

**Input:** One `Section` at a time (iterates through list)
**Output:** `DistilledSection`

**LLM Provider Selection:**
```python
# Configurable in .env or config.yaml
LLM_PROVIDER = "gemini"   # "gemini" | "openai"
GEMINI_MODEL = "gemini-1.5-pro"
OPENAI_MODEL = "gpt-4o"

# Optional: use different models per task
DISTILL_MODEL = "gemini-1.5-pro"
VALIDATE_MODEL = "gpt-4o-mini"
```

**The Distillation Prompt (Core of the System):**

```
You are a Knowledge Distiller for technical and academic content.

Your job is NOT to summarize. Your job is to DISTILL.

Rules:
1. Extract EVERY distinct concept, term, algorithm, formula, or principle — 
   do not skip anything important.
2. Remove: repeated explanations, padding, motivating stories, redundant 
   examples, and filler content.
3. Rewrite each concept in clear, simple language — 1 to 3 sentences maximum.
4. Add ONE practical, concrete example per concept that makes it instantly 
   understandable. Make the example real and relatable.
5. For code or formulas: preserve them exactly as-is, then explain beneath.
6. Do NOT merge two different concepts into one point.
7. Output ONLY in the exact format below — no preamble, no conclusion.

Output Format:
---
## {Section Title}

**{Concept Name}**
→ {Clear explanation in 1-3 sentences}
→ Example: {Concrete, relatable example}

**{Next Concept Name}**
→ ...
---

Section Title: {title}
Section Text:
{section_text}
```

**Output Schema:**
```python
class DistilledSection(TypedDict):
    index: int
    title: str
    distilled_markdown: str   # AI output in the defined format
    image_paths: list[str]    # Paths to images from this section
    original_word_count: int
    distilled_word_count: int
    concepts_found: int       # Count of bold concept headers in output
```

**Error Handling:**
- Retry up to 3 times on API failure with exponential backoff
- If section text > model context limit: split at paragraph boundary, distill in parts, merge
- Log token usage per section

---

### Node 5 — Output Writer

**Input:** `DistilledSection`
**Output:** Appended `.md` file

**Responsibilities:**
- On first section: create output file with document header block
- On each section: append distilled markdown + image references
- After each append: flush to disk (so progress is saved even if pipeline fails midway)

**Output File Structure:**
```markdown
# {Document Title}
> **Source:** {file_path}
> **Processed:** {timestamp}
> **Provider:** Gemini 1.5 Pro
> **Total Sections:** {n}

---

## Chapter 1 — Introduction to Operating Systems

**Process**
→ A process is a running instance of a program with its own memory space and CPU state.
→ Example: Opening Chrome twice creates two separate processes — each has its own RAM,
  and crashing one doesn't affect the other.

**Context Switch**
→ The OS saves the current process state (registers, program counter) and loads another 
  process's state to switch between them.
→ Example: Like pausing a video game, saving your progress, and loading a friend's save 
  file — then switching back later right where you left off.

![Figure 1.1 — Process State Diagram](./images/os_book/02_1.png)

---

## Chapter 2 — CPU Scheduling

...
```

**Config Options:**
```yaml
output:
  dir: "./output"
  filename: "{document_title}_distilled.md"
  image_link_style: "relative"   # "relative" | "absolute"
  add_section_divider: true      # Add --- between sections
  add_word_count_stats: false    # Optionally add "Reduced from 2400 → 310 words"
```

---

### Node 6 — Quality Validator (Optional)

**Input:** `DistilledSection`
**Output:** Validation report or flag to re-process

**Checks:**
- `concepts_found >= 1` — at least one concept extracted
- `distilled_word_count >= 50` — not suspiciously empty
- `distilled_word_count <= original_word_count * 0.7` — actually reduced
- Optionally run a second LLM call to verify no key concepts were dropped

---

## 5. State Schema (Full LangGraph State)

```python
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph

class PipelineState(TypedDict):
    # Input
    file_path: str
    config: dict

    # After Node 1
    document: DocumentState

    # After Node 2
    sections: List[Section]
    total_sections: int

    # Processing cursor
    current_section_index: int

    # After Node 4 & 5
    distilled_sections: List[DistilledSection]
    output_file_path: str

    # Tracking
    errors: List[dict]
    token_usage: dict       # {section_index: {input_tokens, output_tokens}}
    processing_complete: bool
```

---

## 6. Configuration File (`config.yaml`)

```yaml
# LLM Provider
llm:
  provider: "gemini"              # "gemini" | "openai"
  gemini_model: "gemini-1.5-pro"
  openai_model: "gpt-4o"
  temperature: 0.3                # Low = consistent, structured output
  max_retries: 3

# Splitting
splitter:
  strategy: "auto"                # "auto" | "heading" | "page_chunk"
  min_section_words: 200
  max_section_words: 8000
  fallback_page_chunk: 10

# Images
image_extractor:
  enabled: true
  min_image_width: 100
  min_image_height: 100

# Output
output:
  dir: "./output"
  format: "md"                    # Only "md" supported for now
  add_section_divider: true
  add_stats_footer: false

# Validation
validator:
  enabled: false                  # Set to true for quality checking
  model: "gpt-4o-mini"           # Can use a cheaper model here
```

---

## 7. Project Folder Structure

```
knowledge-distiller/
│
├── main.py                      # Entry point — run pipeline
├── config.yaml                  # User configuration
├── .env                         # API keys (GEMINI_API_KEY, OPENAI_API_KEY)
├── requirements.txt
│
├── pipeline/
│   ├── graph.py                 # LangGraph graph definition
│   ├── state.py                 # PipelineState TypedDict
│   └── nodes/
│       ├── loader.py            # Node 1
│       ├── splitter.py          # Node 2
│       ├── image_extractor.py   # Node 3
│       ├── distiller.py         # Node 4
│       ├── writer.py            # Node 5
│       └── validator.py         # Node 6
│
├── prompts/
│   └── distill.txt              # The distillation prompt (editable)
│
├── providers/
│   ├── base.py                  # Abstract LLM provider interface
│   ├── gemini.py                # Google Gemini implementation
│   └── openai.py                # OpenAI implementation
│
├── output/                      # Generated at runtime
│   ├── {book_title}_distilled.md
│   └── images/
│       └── {book_slug}/
│           └── {section}_{n}.png
│
└── tests/
    ├── test_splitter.py
    ├── test_distiller.py
    └── sample_docs/
```

---

## 8. CLI Usage

```bash
# Basic usage
python main.py --file ./books/os_concepts.pdf

# Specify provider
python main.py --file ./books/deep_learning.pdf --provider openai

# Custom output location
python main.py --file ./books/clean_code.pdf --output ./my_notes/

# Disable image extraction
python main.py --file ./books/algorithms.pdf --no-images

# Process only specific chapters (by index)
python main.py --file ./books/dsa.pdf --sections 3,4,5
```

---

## 9. Python Dependencies

```
langgraph>=0.2.0
langchain-google-genai>=1.0.0
langchain-openai>=0.1.0
langchain-core>=0.2.0
PyMuPDF>=1.24.0          # PDF parsing + image extraction
ebooklib>=0.18           # EPUB parsing
python-docx>=1.1.0       # DOCX parsing
Pillow>=10.0.0           # Image processing
pydantic>=2.0.0
pydantic-settings>=2.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
tiktoken>=0.7.0          # Token counting
rich>=13.0.0             # CLI progress display
```

---

## 10. Key Design Decisions & Rationale

| Decision | Reason |
|---|---|
| **Section-by-section processing** | Avoids context limit issues; progress saved after each section |
| **Append-on-write output** | If pipeline crashes at section 8/20, sections 1–7 are already saved |
| **Prompt in external file** | Easy to tweak the distillation behavior without touching code |
| **Provider abstraction layer** | Swap Gemini ↔ OpenAI without changing any node logic |
| **Image copy (not re-render)** | Diagrams are kept as-is — no AI interpretation of visuals |
| **LangGraph over simple loop** | Enables conditional edges (e.g., re-process if quality check fails), streaming, and observability |
| **Low temperature (0.3)** | Consistent structured output format; avoids creative drift in distillation |

---

## 11. Out of Scope (v1)

- GUI or web interface (CLI only for v1)
- OCR for scanned PDFs (text-based PDFs only)
- Audio/video input
- Multi-language output (prompt can be adjusted manually)
- Cloud storage integration
- Real-time streaming of output to terminal
