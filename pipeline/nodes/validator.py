from pipeline.state import PipelineState

def validator_node(state: PipelineState) -> PipelineState:
    """Node 6: Validate the quality of the distilled section."""
    if not state["distilled_sections"]:
        return state

    last_distilled = state["distilled_sections"][-1]
    original_words = last_distilled["original_word_count"]
    distilled_words = last_distilled["distilled_word_count"]
    concepts = last_distilled["concepts_found"]

    is_valid = True
    reasons = []

    if concepts < 1:
        is_valid = False
        reasons.append("No concepts found")

    if distilled_words < 50 and original_words > 200:
        is_valid = False
        reasons.append("Suspiciously short output")

    if distilled_words > original_words * 0.9:
        # Not really a failure, but maybe a warning
        pass

    if not is_valid:
        state["errors"].append({
            "node": "validator",
            "section": state["current_section_index"],
            "reasons": reasons
        })

    # Increment index regardless for now, or we could loop back if we want to retry
    state["current_section_index"] += 1
    
    if state["current_section_index"] >= state["total_sections"]:
        state["processing_complete"] = True

    return state
