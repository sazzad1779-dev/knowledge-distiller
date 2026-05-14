# Node 4: AI Distiller

The Distiller node is the "brain" of the system. It uses Large Language Models to transform dense technical text into compact, concept-focused knowledge.

## Core Philosophy: Distillation vs. Summarization
- **Summarization**: Shortens text by picking the most "important" parts. Often loses technical nuances.
- **Distillation**: Keeps **every** unique concept but removes redundant explanations, filler words, and motivating stories. Each concept is then re-explained clearly with a concrete example.

## LLM Configuration

The system supports multiple providers via an abstraction layer:
- **Google Gemini**: Primary choice (Gemini 1.5 Pro).
- **OpenAI**: Secondary choice (GPT-4o).

```python
# .env configuration
GEMINI_API_KEY=xxx
OPENAI_API_KEY=yyy
LLM_PROVIDER=gemini
```

## The Distillation Prompt
The prompt (stored in `prompts/distill.txt`) enforces a strict structure:
1. **Concept Name** (Bold)
2. **Explanation**: 1-3 sentences of clear, simple language.
3. **Example**: A practical, relatable, concrete scenario.
4. **Code/Formulas**: Preserved exactly as-is.

## Token Management & Retries
- **Large Sections**: If a section exceeds the model's context window, it is split into sub-chunks, distilled independently, and then merged.
- **Retries**: 3-stage exponential backoff for API rate limits or transient errors.
