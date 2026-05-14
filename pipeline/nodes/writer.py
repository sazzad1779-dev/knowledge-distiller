import os
from datetime import datetime
from pipeline.state import PipelineState

def writer_node(state: PipelineState) -> PipelineState:
    """Node 5: Append distilled content to the output Markdown file.

    Each section is immediately flushed and fsync'd to disk after distillation,
    so progress is preserved even if the pipeline is interrupted mid-run.
    On the first section the file is created with a header; all subsequent
    sections are appended to the same file.
    """
    idx = state["current_section_index"]
    if idx >= len(state["distilled_sections"]):
        return {}

    distilled = state["distilled_sections"][-1]
    output_config = state["config"].get("output", {})
    output_dir = output_config.get("dir", "./output")
    os.makedirs(output_dir, exist_ok=True)

    output_path = state.get("output_file_path")

    if not output_path:
        # First section — create the output file with a header
        doc_title = state["document"]["metadata"].get("title", "Untitled")
        while isinstance(doc_title, (list, tuple)) and doc_title:
            doc_title = doc_title[0]

        if not isinstance(doc_title, str):
            doc_title = str(doc_title)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{doc_title.replace(' ', '_').lower()}_distilled.md"
        output_path = os.path.join(output_dir, filename)

        provider = state["config"].get("llm", {}).get("provider", "gemini")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {doc_title}\n")
            f.write(f"> **Source:** {state['file_path']}\n")
            f.write(f"> **Processed:** {timestamp}\n")
            f.write(f"> **Provider:** {provider.capitalize()}\n")
            f.write(f"> **Total Sections:** {state['total_sections']}\n\n")
            f.write("---\n\n")

    # Append the freshly distilled section immediately
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(distilled["distilled_markdown"])
        f.write("\n\n")

        # Add image references not already embedded by the LLM
        markdown_content = distilled["distilled_markdown"]
        for img_path in distilled.get("image_paths", []):
            img_filename = os.path.basename(img_path)
            if img_filename not in markdown_content or f"({img_filename})" not in markdown_content:
                rel_path = os.path.relpath(img_path, os.path.dirname(output_path))
                f.write(f"![Image]({rel_path})\n\n")

        if output_config.get("add_section_divider", True):
            f.write("---\n\n")

        # Guarantee the bytes hit disk before the next section starts
        f.flush()
        os.fsync(f.fileno())

    # Return only the keys that changed so LangGraph merges them into shared state
    return {"output_file_path": output_path}
