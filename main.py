import os
import argparse
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
    TimeRemainingColumn
)
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

    # Initialize state
    initial_state: PipelineState = {
        "file_path": file_path,
        "config": config,
        "document": None,
        "sections": [],
        "total_sections": 0,
        "current_section_index": 0,
        "distilled_sections": [],
        "output_file_path": None,
        "errors": [],
        "token_usage": {},
        "processing_complete": False
    }

    # Create and run graph
    app = create_graph()
    
    console.print(f"[bold blue]Starting Knowledge Distiller for:[/bold blue] {file_path}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Initializing...", total=None)
        
        final_state = initial_state
        
        # Use stream() to get updates from each node
        for output in app.stream(initial_state):
            # output is a dict: {node_name: state_updates}
            for node_name, state_update in output.items():
                # Update our local tracking state
                final_state.update(state_update)
                
                # Update total if we just split the document
                if "total_sections" in state_update:
                    total = state_update["total_sections"]
                    progress.update(task, total=total)
                
                # Determine description and completion status
                current_idx = final_state.get("current_section_index", 0)
                total_sections = final_state.get("total_sections", 0)
                
                if node_name == "loader":
                    doc = state_update.get("document", {})
                    progress.console.log(f"[bold green]✓[/bold green] Loaded document: [cyan]{doc.get('file_path')}[/cyan] ({len(doc.get('pages', []))} pages)")
                    progress.update(task, description="[cyan]Loading document...[/cyan]")
                elif node_name == "splitter":
                    num_sections = state_update.get("total_sections", 0)
                    progress.console.log(f"[bold green]✓[/bold green] Split into [bold]{num_sections}[/bold] sections")
                    progress.update(task, description="[cyan]Splitting into sections...[/cyan]")
                elif node_name == "image_extractor":
                    progress.update(task, description=f"[cyan]Extracting images (Section {current_idx + 1}/{total_sections})...[/cyan]")
                elif node_name == "distiller":
                    # Get the last distilled section
                    if "distilled_sections" in state_update and state_update["distilled_sections"]:
                        last_distilled = state_update["distilled_sections"][-1]
                        title = last_distilled.get("title", "Unknown")
                        words = last_distilled.get("distilled_word_count", 0)
                        concepts = last_distilled.get("concepts_found", 0)
                        progress.console.log(f"[bold blue]AI[/bold blue] Distilled: [bold]{title}[/bold] ([magenta]{words} words[/magenta], [yellow]{concepts} concepts[/yellow])")
                    
                    progress.update(task, description=f"[cyan]Distilling section {current_idx + 1}/{total_sections}...[/cyan]")
                elif node_name == "writer":
                    progress.update(task, description=f"[cyan]Saving section {current_idx + 1}/{total_sections}...[/cyan]")
                elif node_name == "validator":
                    # If there are errors in this node, they will be logged later, 
                    # but we can log success here
                    # current_idx is now incremented (e.g., 1 after first section)
                    if final_state.get("processing_complete"):
                        progress.update(task, completed=current_idx, description="[bold green]All sections processed![/bold green]")
                    else:
                        progress.update(task, completed=current_idx, description=f"[cyan]Section {current_idx}/{total_sections} validated. Starting next...[/cyan]")
        
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
