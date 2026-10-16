# ADR-0005: Grounded generation with a small model

**Date**: 2026-10-16
**Status**: accepted
**Deciders**: Phone Myint San

## Context

The generation step must answer from the retrieved chunks without inventing facts.
LLMs default to answering from training data, which silently produces plausible but
unverifiable answers — the main failure mode RAG exists to prevent.

## Decision

We use `gpt-4o-mini` with a system prompt that restricts it to the provided context
("Answer using ONLY the provided context... say you don't know"), and we return the
source filenames alongside every answer.

## Alternatives Considered

### Alternative 1: Larger model (gpt-4o / o-series)
- **Pros**: better reasoning over conflicting or subtle context
- **Cons**: 10–20x the cost per question
- **Why not**: grounded question-answering is reading comprehension; the small model handles it, and the model name is a one-line change if it doesn't

### Alternative 2: No grounding instruction (just prepend context)
- **Pros**: slightly shorter prompt
- **Cons**: the model blends context with training data and answers even when the context says nothing
- **Why not**: silent hallucination is exactly what this tool must not do

## Consequences

### Positive
- "I don't know" is a possible and correct output
- Source filenames make every answer checkable by the user

### Negative
- Over-strict grounding can refuse questions a human could answer by combining chunks
- Prompt-level grounding is a strong instruction, not a guarantee

### Risks
- For higher assurance, add a verification pass (answer -> does the context support
  each claim?) or citation-per-sentence. Not needed for a personal tool.
