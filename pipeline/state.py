from typing import TypedDict, List, Optional, Dict, Any

class PageData(TypedDict):
    page_num: int
    text: str
    has_images: bool

class DocumentState(TypedDict):
    file_path: str
    file_type: str         # "pdf" | "epub" | "docx" | "txt"
    raw_text: str
    metadata: Dict[str, Any]         # title, author, pages
    pages: List[PageData]  # [{page_num, text, has_images}]

class Section(TypedDict):
    index: int
    title: str             # Extracted or generated heading
    text: str              # Full raw text of the section
    page_start: int
    page_end: int
    word_count: int
    has_images: bool       # Whether images exist in this page range
    image_paths: Optional[List[str]]

class DistilledSection(TypedDict):
    index: int
    title: str
    distilled_markdown: str   # AI output in the defined format
    image_paths: List[str]    # Paths to images from this section
    original_word_count: int
    distilled_word_count: int
    concepts_found: int       # Count of bold concept headers in output

class PipelineState(TypedDict):
    # Input
    file_path: str
    config: Dict[str, Any]

    # After Node 1
    document: Optional[DocumentState]

    # After Node 2
    sections: List[Section]
    total_sections: int

    # Processing cursor
    current_section_index: int

    # After Node 4 & 5
    distilled_sections: List[DistilledSection]
    output_file_path: Optional[str]

    # Tracking
    errors: List[Dict[str, Any]]
    token_usage: Dict[int, Dict[str, int]]       # {section_index: {input_tokens, output_tokens}}
    processing_complete: bool
