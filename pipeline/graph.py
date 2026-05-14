from langgraph.graph import StateGraph, END
from pipeline.state import PipelineState
from pipeline.nodes.loader import loader_node
from pipeline.nodes.splitter import splitter_node
from pipeline.nodes.image_extractor import image_extractor_node
from pipeline.nodes.distiller import distiller_node
from pipeline.nodes.writer import writer_node
from pipeline.nodes.validator import validator_node

def create_graph():
    # Initialize the graph
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("loader", loader_node)
    workflow.add_node("splitter", splitter_node)
    workflow.add_node("image_extractor", image_extractor_node)
    workflow.add_node("distiller", distiller_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("validator", validator_node)

    # Define edges
    workflow.set_entry_point("loader")
    
    workflow.add_edge("loader", "splitter")
    workflow.add_edge("splitter", "image_extractor")
    workflow.add_edge("image_extractor", "distiller")
    workflow.add_edge("distiller", "writer")
    workflow.add_edge("writer", "validator")

    # Conditional edge from validator
    def should_continue(state: PipelineState):
        if state.get("processing_complete") or state.get("errors") and any(e.get("node") == "loader" for e in state["errors"]):
            return "end"
        return "continue"

    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "continue": "distiller",
            "end": END
        }
    )

    return workflow.compile()
