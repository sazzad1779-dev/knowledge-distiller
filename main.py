import os
import argparse
import yaml
from dotenv import load_dotenv
from tqdm import tqdm
from rich.console import Console
from pipeline.graph import create_graph
from pipeline.state import PipelineState

# Load environment variables
load_dotenv()

console = Console()

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_pipeline(file_path: str, provider: str = None, output_dir: str = None):
    # Load configuration
    config = load_config("config.yaml")
    if provider:
        config["llm"]["provider"] = provider
    if output_dir:
        config["output"]["dir"] = output_dir

    # Check for progress to resume
    output_dir_resolved = config.get("output", {}).get("dir", "./output")
    base_name, _ = os.path.splitext(os.path.basename(file_path))
    expected_output_path = os.path.join(output_dir_resolved, f"{base_name}.md")
    expected_progress_path = f"{expected_output_path}.progress"
    
    resume_index = 0
    if os.path.exists(expected_progress_path) and os.path.exists(expected_output_path):
        try:
            with open(expected_progress_path, "r") as f:
                resume_index = int(f.read().strip()) + 1
            console.print(f"[bold yellow]Found existing progress. Resuming from section {resume_index}[/bold yellow]")
        except Exception:
            resume_index = 0

    # Initialize state
    initial_state: PipelineState = {
        "file_path": file_path,
        "config": config,
        "document": None,
        "sections": [],
        "total_sections": 0,
        "current_section_index": resume_index,
        "distilled_sections": [],
        "output_file_path": expected_output_path if resume_index > 0 else None,
        "errors": [],
        "token_usage": {},
        "processing_complete": False
    }

    # Create and run graph
    app = create_graph()
    
    console.print(f"[bold blue]Starting Knowledge Distiller for:[/bold blue] {file_path}")
    
    final_state = initial_state
    pbar = None

    def log_message(msg):
        if pbar:
            with console.capture() as capture:
                console.print(msg)
            pbar.write(capture.get().strip())
        else:
            console.print(msg)

    try:
        # Use stream() to get updates from each node
        for output in app.stream(initial_state):
            # output is a dict: {node_name: state_updates}
            for node_name, state_update in output.items():
                # Update our local tracking state
                if state_update is not None:
                    final_state.update(state_update)
                
                # Determine description and completion status
                current_idx = final_state.get("current_section_index", 0)
                total_sections = final_state.get("total_sections", 0)
                
                if node_name == "loader":
                    doc = state_update.get("document", {})
                    log_message(f"[bold green]✓[/bold green] Loaded document: [cyan]{doc.get('file_path')}[/cyan] ({len(doc.get('pages', []))} pages)")
                elif node_name == "splitter":
                    num_sections = state_update.get("total_sections", 0)
                    log_message(f"[bold green]✓[/bold green] Split into [bold]{num_sections}[/bold] sections")
                    
                    current_idx_for_pbar = final_state.get("current_section_index", 0)
                    # Initialize tqdm progress bar now that we know the total sections
                    pbar = tqdm(
                        total=num_sections,
                        initial=current_idx_for_pbar,
                        desc="Processing",
                        unit="section",
                        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
                    )
                elif node_name == "image_extractor":
                    if pbar:
                        pbar.set_description(f"Extracting images (Section {current_idx + 1}/{total_sections})")
                elif node_name == "distiller":
                    # Get the last distilled section
                    if "distilled_sections" in state_update and state_update["distilled_sections"]:
                        last_distilled = state_update["distilled_sections"][-1]
                        title = last_distilled.get("title", "Unknown")
                        words = last_distilled.get("distilled_word_count", 0)
                        concepts = last_distilled.get("concepts_found", 0)
                        log_message(f"[bold blue]AI[/bold blue] Distilled: [bold]{title}[/bold] ([magenta]{words} words[/magenta], [yellow]{concepts} concepts[/yellow])")
                    
                    if pbar:
                        pbar.set_description(f"Distilling section {current_idx + 1}/{total_sections}")
                elif node_name == "writer":
                    if pbar:
                        pbar.set_description(f"Saving section {current_idx + 1}/{total_sections}")
                elif node_name == "validator":
                    if pbar:
                        pbar.n = current_idx
                        pbar.refresh()
                        if final_state.get("processing_complete"):
                            pbar.set_description("All sections processed!")
                        else:
                            pbar.set_description(f"Section {current_idx}/{total_sections} validated. Starting next...")
    finally:
        if pbar:
            pbar.close()
        
    if final_state["errors"]:
        console.print("\n[bold red]Errors encountered during processing:[/bold red]")
        for error in final_state["errors"]:
            console.print(f"- {error}")
    
    if final_state["processing_complete"]:
        console.print(f"\n[bold green]Distillation complete![/bold green]")
        console.print(f"Output saved to: [cyan]{final_state['output_file_path']}[/cyan]")
    else:
        console.print("\n[bold yellow]Processing ended prematurely.[/bold yellow]")

def main():
    parser = argparse.ArgumentParser(description="Knowledge Distiller — Technical Book Distillation Pipeline")
    parser.add_argument("--file", required=True, help="Path to the source document (PDF, EPUB, DOCX, TXT)")
    parser.add_argument("--provider", choices=["gemini", "openai", "mock"], help="Override LLM provider")
    parser.add_argument("--output", help="Override output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        console.print(f"[bold red]Error:[/bold red] File not found: {args.file}")
        return

    run_pipeline(args.file, args.provider, args.output)

if __name__ == "__main__":
    main()
