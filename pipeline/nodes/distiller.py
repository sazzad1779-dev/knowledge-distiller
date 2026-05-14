import os
from pipeline.state import PipelineState, DistilledSection
from providers.gemini import GeminiProvider
from providers.openai import OpenAIProvider

def distiller_node(state: PipelineState) -> PipelineState:
    """Node 4: Distill a single section using AI."""
    idx = state["current_section_index"]
    if idx >= len(state["sections"]):
        return state

    section = state["sections"][idx]
    
    # Initialize Provider
    provider_name = state["config"].get("llm", {}).get("provider", "gemini")
    temperature = state["config"].get("llm", {}).get("temperature", 0.3)
    
    if provider_name == "gemini":
        model = state["config"].get("llm", {}).get("gemini_model", "gemini-2.5-flash")
        provider = GeminiProvider(model=model, temperature=temperature)
    elif provider_name == "openai":
        model = state["config"].get("llm", {}).get("openai_model", "gpt-4o")
        provider = OpenAIProvider(model=model, temperature=temperature)
    elif provider_name == "mock":
        from providers.mock import MockLLMProvider
        provider = MockLLMProvider()
    else:
        state["errors"].append({"node": "distiller", "error": f"Unknown provider: {provider_name}"})
        return state

    # Load Prompt
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "distill.txt")
    with open(prompt_path, "r") as f:
        prompt_template = f.read()

    # Format Prompt
    images_info = ", ".join([os.path.basename(p) for p in section.get("image_paths", [])]) if section.get("image_paths") else "None"
    
    prompt = prompt_template.format(
        title=section["title"],
        images=images_info,
        section_text=section["text"]
    )

    # Logging is handled by the progress display in main.py

    try:
        distilled_content = provider.generate(prompt)
        
        # Simple extraction of concepts found (counting bold markers)
        concepts_found = distilled_content.count("**") // 2
        
        distilled_section: DistilledSection = {
            "index": idx,
            "title": section["title"],
            "distilled_markdown": distilled_content,
            "image_paths": section.get("image_paths", []),
            "original_word_count": section["word_count"],
            "distilled_word_count": len(distilled_content.split()),
            "concepts_found": concepts_found
        }
        
        state["distilled_sections"].append(distilled_section)
        
        # Track token usage (simplified)
        state["token_usage"][idx] = {
            "input": provider.get_token_count(prompt),
            "output": provider.get_token_count(distilled_content)
        }
        
    except Exception as e:
        state["errors"].append({"node": "distiller", "section": idx, "error": str(e)})

    return state
