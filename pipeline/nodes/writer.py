import os
from datetime import datetime
from pipeline.state import PipelineState

def writer_node(state: PipelineState) -> PipelineState:
    """Node 5: Append distilled content to the output Markdown file."""
    idx = state["current_section_index"]
    if idx >= len(state["distilled_sections"]):
        return state

    distilled = state["distilled_sections"][-1]
    output_config = state["config"].get("output", {})
    output_dir = output_config.get("dir", "./output")
    os.makedirs(output_dir, exist_ok=True)

    if not state["output_file_path"]:
        # Initialize output file
        doc_title = state["document"]["metadata"].get("title", "Untitled")
        while isinstance(doc_title, (list, tuple)) and doc_title:
            doc_title = doc_title[0]
        
        if not isinstance(doc_title, str):
            doc_title = str(doc_title)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{doc_title.replace(' ', '_').lower()}_distilled.md"
        output_path = os.path.join(output_dir, filename)
        state["output_file_path"] = output_path
        
        provider = state["config"].get("llm", {}).get("provider", "gemini")
        
        with open(output_path, "w") as f:
            f.write(f"# {doc_title}\n")
            f.write(f"> **Source:** {state['file_path']}\n")
            f.write(f"> **Processed:** {timestamp}\n")
            f.write(f"> **Provider:** {provider.capitalize()}\n")
            f.write(f"> **Total Sections:** {state['total_sections']}\n\n")
            f.write("---\n\n")

    output_path = state["output_file_path"]
    
    with open(output_path, "a") as f:
        f.write(distilled["distilled_markdown"])
        f.write("\n\n")
        
        # Add image references
        for img_path in distilled["image_paths"]:
            # Make path relative to output file if needed
            rel_path = os.path.relpath(img_path, os.path.dirname(output_path))
            f.write(f"![Image]({rel_path})\n\n")
            
        if output_config.get("add_section_divider", True):
            f.write("---\n\n")

    return state
