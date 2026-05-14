import os
import fitz  # PyMuPDF
from typing import Dict, Any, List
from pipeline.state import PipelineState, DocumentState, PageData

def loader_node(state: PipelineState) -> PipelineState:
    """Node 1: Load the document and extract raw text and metadata."""
    file_path = state["file_path"]
    if not os.path.exists(file_path):
        state["errors"].append({"node": "loader", "error": f"File not found: {file_path}"})
        return state

    file_ext = os.path.splitext(file_path)[1].lower()
    doc_state: DocumentState = {
        "file_path": file_path,
        "file_type": file_ext[1:],
        "raw_text": "",
        "metadata": {},
        "pages": []
    }

    try:
        if file_ext == ".pdf":
            doc_state = _load_pdf(file_path, doc_state)
        elif file_ext == ".epub":
            doc_state = _load_epub(file_path, doc_state)
        elif file_ext == ".docx":
            doc_state = _load_docx(file_path, doc_state)
        elif file_ext in [".txt", ".md"]:
            doc_state = _load_text(file_path, doc_state)
        else:
            state["errors"].append({"node": "loader", "error": f"Unsupported file type: {file_ext}"})
            return state
        
        state["document"] = doc_state
    except Exception as e:
        state["errors"].append({"node": "loader", "error": str(e)})

    return state

def _load_pdf(file_path: str, doc_state: DocumentState) -> DocumentState:
    doc = fitz.open(file_path)
    doc_state["metadata"] = doc.metadata
    doc_state["metadata"]["pages"] = len(doc)
    
    full_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        full_text.append(text)
        doc_state["pages"].append({
            "page_num": i + 1,
            "text": text,
            "has_images": len(page.get_images()) > 0
        })
    
    doc_state["raw_text"] = "\n".join(full_text)
    return doc_state

def _load_epub(file_path: str, doc_state: DocumentState) -> DocumentState:
    from ebooklib import epub
    from bs4 import BeautifulSoup
    import ebooklib

    book = epub.read_epub(file_path)
    doc_state["metadata"] = {
        "title": book.get_metadata('DC', 'title'),
        "creator": book.get_metadata('DC', 'creator'),
    }
    
    full_text = []
    page_num = 1
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text()
            full_text.append(text)
            doc_state["pages"].append({
                "page_num": page_num,
                "text": text,
                "has_images": len(soup.find_all('img')) > 0
            })
            page_num += 1
            
    doc_state["raw_text"] = "\n".join(full_text)
    doc_state["metadata"]["pages"] = page_num - 1
    return doc_state

def _load_docx(file_path: str, doc_state: DocumentState) -> DocumentState:
    from docx import Document
    doc = Document(file_path)
    
    full_text = []
    # DOCX doesn't have native "pages" in the same way PDFs do, 
    # so we treat each paragraph or group of paragraphs as a "page" 
    # for consistent structure, or just one big page.
    # For now, let's group by every 500 words as a "page" fallback.
    
    text = "\n".join([para.text for para in doc.paragraphs])
    doc_state["raw_text"] = text
    doc_state["metadata"] = {"title": os.path.basename(file_path)}
    
    # Simple chunking for DOCX "pages"
    words = text.split()
    chunk_size = 500
    for i in range(0, len(words), chunk_size):
        chunk_text = " ".join(words[i:i+chunk_size])
        doc_state["pages"].append({
            "page_num": (i // chunk_size) + 1,
            "text": chunk_text,
            "has_images": False # Complex to detect in docx without more logic
        })
        
    doc_state["metadata"]["pages"] = len(doc_state["pages"])
    return doc_state

def _load_text(file_path: str, doc_state: DocumentState) -> DocumentState:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    doc_state["raw_text"] = text
    doc_state["metadata"] = {"title": os.path.basename(file_path)}
    
    # Simple chunking for text "pages"
    words = text.split()
    chunk_size = 500
    for i in range(0, len(words), chunk_size):
        chunk_text = " ".join(words[i:i+chunk_size])
        doc_state["pages"].append({
            "page_num": (i // chunk_size) + 1,
            "text": chunk_text,
            "has_images": False
        })
        
    doc_state["metadata"]["pages"] = len(doc_state["pages"])
    return doc_state
