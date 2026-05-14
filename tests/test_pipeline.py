import os
import sys
import yaml
from pipeline.graph import create_graph
from pipeline.state import PipelineState

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_full_pipeline():
    # Setup paths
    sample_file = os.path.join(os.path.dirname(__file__), "sample_docs", "sample_doc.md")
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    
    # Load config and override for test
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    
    config["llm"]["provider"] = "mock"
    config["output"]["dir"] = "./test_output"
    
    # Initialize state
    initial_state: PipelineState = {
        "file_path": sample_file,
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
    print(f"Running pipeline for {sample_file}...")
    
    final_state = app.invoke(initial_state)
    
    # Assertions
    if final_state["errors"]:
        print("Errors encountered:")
        for error in final_state["errors"]:
            print(f"- {error}")
        return False
        
    if not final_state["processing_complete"]:
        print("Pipeline did not complete successfully.")
        return False
        
    if not os.path.exists(final_state["output_file_path"]):
        print(f"Output file not found at {final_state['output_file_path']}")
        return False
        
    print(f"Success! Output saved to: {final_state['output_file_path']}")
    return True

if __name__ == "__main__":
    if test_full_pipeline():
        print("\nPipeline test passed!")
        sys.exit(0)
    else:
        print("\nPipeline test failed!")
        sys.exit(1)
