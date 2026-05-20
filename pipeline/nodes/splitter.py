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
    max_words = config.get("max_section_words", 1500)
    fallback_pages = config.get("fallback_page_chunk", 10)

    sections = []
    
    # Priority 1 & 2: Heading detection (simplified for now)
    # We'll look for common chapter/section patterns in the text
    content = doc["raw_text"]
    
    # Pattern for "Chapter X", "Section X", "Part X" or markdown headings
    heading_pattern = r'(?m)^(?:#{1,3}\s+.+|Chapter\s+\d+.*|Section\s+\d+.*|Part\s+\d+.*)$'
    
    matches = list(re.finditer(heading_pattern, content))
    pages = doc["pages"]
    
    # Build page character offset boundaries
    page_offsets = []
    current_offset = 0
    for p in pages:
        p_text = p["text"]
        start_char = current_offset
        end_char = current_offset + len(p_text)
        page_offsets.append((p["page_num"], start_char, end_char))
        current_offset += len(p_text) + 1  # +1 for the "\n" join separator

    def map_pos_to_pages(start_pos, end_pos):
        page_start = 1
        page_end = len(pages)
        for p_num, s_char, e_char in page_offsets:
            if start_pos >= s_char and start_pos <= e_char:
                page_start = p_num
            if end_pos >= s_char and end_pos <= e_char:
                page_end = p_num
        return page_start, page_end

    if matches:
        for i in range(len(matches)):
            start_pos = matches[i].start()
            end_pos = matches[i+1].start() if i+1 < len(matches) else len(content)
            
            title = matches[i].group(0).strip()
            section_text = content[start_pos:end_pos].strip()
            
            # Split the section text by paragraphs
            paragraph_texts = re.split(r'\n\s*\n', section_text)
            paragraphs = []
            search_start = start_pos
            for p_text in paragraph_texts:
                if not p_text.strip():
                    continue
                p_start = content.find(p_text, search_start)
                if p_start == -1:
                    p_start = search_start
                p_end = p_start + len(p_text)
                paragraphs.append({
                    "text": p_text,
                    "start": p_start,
                    "end": p_end
                })
                search_start = p_end
                
            # If no paragraphs found (e.g. single block of text), fallback to a single paragraph
            if not paragraphs:
                paragraphs = [{
                    "text": section_text,
                    "start": start_pos,
                    "end": end_pos
                }]
                
            # Group paragraphs into chunks of <= max_words
            chunks = []
            current_chunk_paras = []
            current_chunk_words = 0
            
            for p in paragraphs:
                p_words = len(p["text"].split())
                if current_chunk_words + p_words > max_words and current_chunk_paras:
                    chunks.append(current_chunk_paras)
                    current_chunk_paras = [p]
                    current_chunk_words = p_words
                else:
                    current_chunk_paras.append(p)
                    current_chunk_words += p_words
            
            if current_chunk_paras:
                chunks.append(current_chunk_paras)
                
            # Append each chunk as a separate section
            for chunk_idx, chunk in enumerate(chunks):
                chunk_text = "\n\n".join([p["text"] for p in chunk])
                chunk_start = chunk[0]["start"]
                chunk_end = chunk[-1]["end"]
                
                if len(chunks) > 1:
                    chunk_title = f"{title} (Part {chunk_idx + 1})"
                else:
                    chunk_title = title
                    
                page_start, page_end = map_pos_to_pages(chunk_start, chunk_end)
                
                # Check if any page in this range has images
                has_images = any(pages[p_idx]["has_images"] for p_idx in range(page_start - 1, min(page_end, len(pages))))
                
                sections.append({
                    "index": len(sections),
                    "title": chunk_title,
                    "text": chunk_text,
                    "page_start": page_start,
                    "page_end": page_end,
                    "word_count": len(chunk_text.split()),
                    "has_images": has_images,
                    "image_paths": []
                })
    else:
        # Fallback: Dynamic page grouping based on word count
        current_chunk_pages = []
        current_chunk_words = 0
        
        for p in pages:
            p_words = len(p["text"].split())
            if current_chunk_words + p_words > max_words and current_chunk_pages:
                chunk_text = "\n".join([cp["text"] for cp in current_chunk_pages])
                has_images = any([cp["has_images"] for cp in current_chunk_pages])
                sections.append({
                    "index": len(sections),
                    "title": f"Section {len(sections) + 1}",
                    "text": chunk_text,
                    "page_start": current_chunk_pages[0]["page_num"],
                    "page_end": current_chunk_pages[-1]["page_num"],
                    "word_count": len(chunk_text.split()),
                    "has_images": has_images,
                    "image_paths": []
                })
                current_chunk_pages = [p]
                current_chunk_words = p_words
            else:
                current_chunk_pages.append(p)
                current_chunk_words += p_words
                
        if current_chunk_pages:
            chunk_text = "\n".join([cp["text"] for cp in current_chunk_pages])
            has_images = any([cp["has_images"] for cp in current_chunk_pages])
            sections.append({
                "index": len(sections),
                "title": f"Section {len(sections) + 1}",
                "text": chunk_text,
                "page_start": current_chunk_pages[0]["page_num"],
                "page_end": current_chunk_pages[-1]["page_num"],
                "word_count": len(chunk_text.split()),
                "has_images": has_images,
                "image_paths": []
            })

    state["sections"] = sections
    state["total_sections"] = len(sections)
    return state
