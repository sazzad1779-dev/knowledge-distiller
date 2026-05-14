from pipeline.state import PipelineState

def validator_node(state: PipelineState) -> dict:
    """Node 6: Validate the quality of the distilled section and advance the cursor."""
    if not state["distilled_sections"]:
        return {}

    last_distilled = state["distilled_sections"][-1]
    original_words = last_distilled["original_word_count"]
    distilled_words = last_distilled["distilled_word_count"]
    concepts = last_distilled["concepts_found"]

    updates: dict = {}
    errors = list(state.get("errors", []))

    if concepts < 1:
        errors.append({
            "node": "validator",
            "section": state["current_section_index"],
            "reasons": ["No concepts found"]
        })
        updates["errors"] = errors
    elif distilled_words < 50 and original_words > 200:
        errors.append({
            "node": "validator",
            "section": state["current_section_index"],
            "reasons": ["Suspiciously short output"]
        })
        updates["errors"] = errors

    # Advance the section cursor
    next_index = state["current_section_index"] + 1
    updates["current_section_index"] = next_index

    if next_index >= state["total_sections"]:
        updates["processing_complete"] = True

    return updates
