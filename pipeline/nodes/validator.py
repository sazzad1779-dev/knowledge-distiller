from pipeline.state import PipelineState

def validator_node(state: PipelineState) -> dict:
    """Node 6: Validate the quality of the distilled section and advance the cursor."""
    idx = state["current_section_index"]
    updates: dict = {}
    errors = list(state.get("errors", []))

    # Find the distilled section corresponding to the current index
    current_distilled = next((s for s in state["distilled_sections"] if s["index"] == idx), None)

    if not current_distilled:
        # The section failed to distill completely (e.g. API error recorded in distiller node)
        errors.append({
            "node": "validator",
            "section": idx,
            "reasons": ["Section was not distilled due to earlier errors"]
        })
        updates["errors"] = errors
    else:
        original_words = current_distilled["original_word_count"]
        distilled_words = current_distilled["distilled_word_count"]
        concepts = current_distilled["concepts_found"]

        if concepts < 1:
            errors.append({
                "node": "validator",
                "section": idx,
                "reasons": ["No concepts found"]
            })
            updates["errors"] = errors
        elif distilled_words < 50 and original_words > 200:
            errors.append({
                "node": "validator",
                "section": idx,
                "reasons": ["Suspiciously short output"]
            })
            updates["errors"] = errors

    # Always advance the section cursor to avoid infinite loops
    next_index = idx + 1
    updates["current_section_index"] = next_index

    if next_index >= state["total_sections"]:
        updates["processing_complete"] = True

    return updates
