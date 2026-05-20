import os
import fitz
from typing import List
from pipeline.state import PipelineState, Section

def image_extractor_node(state: PipelineState) -> PipelineState:
    """Node 3: Extract images from the document for each section."""
    if not state["config"].get("image_extractor", {}).get("enabled", True):
        return state

    file_path = state["file_path"]
    if not file_path.lower().endswith(".pdf"):
        # Image extraction currently only optimized for PDF via PyMuPDF
        return state

    doc = fitz.open(file_path)
    output_base_dir = state["config"].get("output", {}).get("dir", "./output")
    doc_slug = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_").lower()
    image_dir = os.path.join(output_base_dir, "images", doc_slug)
    os.makedirs(image_dir, exist_ok=True)

    min_width = state["config"].get("image_extractor", {}).get("min_image_width", 100)
    min_height = state["config"].get("image_extractor", {}).get("min_image_height", 100)

    for section in state["sections"]:
        # Skip sections we've already processed (in case of resume)
        if section["index"] < state.get("current_section_index", 0):
            continue

        if not section.get("has_images", False):
            continue

        page_start = section["page_start"]
        page_end = section["page_end"]
        
        # Adjust for 0-indexing if page_start is 1-indexed
        start_idx = max(0, page_start - 1)
        end_idx = page_end if page_end > 0 else start_idx + 1
        
        image_paths = []
        
        for p_idx in range(start_idx, end_idx):
            if p_idx >= len(doc):
                continue
                
            page = doc[p_idx]
            image_list = page.get_images(full=True)
            
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Check dimensions
                width = base_image["width"]
                height = base_image["height"]
                
                if width < min_width or height < min_height:
                    continue
                
                ext = base_image["ext"]
                image_filename = f"sec{section['index']}_p{p_idx+1}_{img_idx}.{ext}"
                image_path = os.path.join(image_dir, image_filename)
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                image_paths.append(image_path)
        
        section["image_paths"] = image_paths
        section["has_images"] = len(image_paths) > 0

    return state
