import os
import argparse
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
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
        console=console
    ) as progress:
        task = progress.add_task("Processing...", total=None)
        
        # Run the graph
        # For simplicity, we just invoke it. In a real app, we might use stream()
        final_state = app.invoke(initial_state)
        
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
