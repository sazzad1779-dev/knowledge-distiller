import re
from typing import List
from pipeline.state import PipelineState, Section, DocumentState

def splitter_node(state: PipelineState) -> PipelineState:
    """Node 2: Split the document into sections."""
    doc = state["document"]
    if not doc:
        state["errors"].append({"node": "splitter", "error": "No document loaded"})
        return state

    config = state["config"].get("splitter", {})
    min_words = config.get("min_section_words", 200)
    max_words = config.get("max_section_words", 8000)
    fallback_pages = config.get("fallback_page_chunk", 10)

    sections = []
    
    # Priority 1 & 2: Heading detection (simplified for now)
    # We'll look for common chapter/section patterns in the text
    content = doc["raw_text"]
    
    # Pattern for "Chapter X", "Section X", "Part X" or markdown headings
    heading_pattern = r'(?m)^(?:#{1,3}\s+.+|Chapter\s+\d+.*|Section\s+\d+.*|Part\s+\d+.*)$'
    
    matches = list(re.finditer(heading_pattern, content))
    
    if matches:
        for i in range(len(matches)):
            start_pos = matches[i].start()
            end_pos = matches[i+1].start() if i+1 < len(matches) else len(content)
            
            title = matches[i].group(0).strip()
            section_text = content[start_pos:end_pos].strip()
            
            # Estimate page range (very rough)
            # In a real app, we'd map character positions back to page numbers
            # For now, let's just use the index
            
            sections.append({
                "index": i,
                "title": title,
                "text": section_text,
                "page_start": 0, # Placeholder
                "page_end": 0,   # Placeholder
                "word_count": len(section_text.split()),
                "has_images": False, # Placeholder
                "image_paths": []
            })
    else:
        # Fallback: Fixed page-count chunking
        pages = doc["pages"]
        for i in range(0, len(pages), fallback_pages):
            chunk_pages = pages[i : i + fallback_pages]
            chunk_text = "\n".join([p["text"] for p in chunk_pages])
            has_images = any([p["has_images"] for p in chunk_pages])
            
            sections.append({
                "index": len(sections),
                "title": f"Section {len(sections) + 1}",
                "text": chunk_text,
                "page_start": chunk_pages[0]["page_num"],
                "page_end": chunk_pages[-1]["page_num"],
                "word_count": len(chunk_text.split()),
                "has_images": has_images,
                "image_paths": []
            })

    # Filter/Merge small sections (optional improvement)
    
    state["sections"] = sections
    state["total_sections"] = len(sections)
    return state
