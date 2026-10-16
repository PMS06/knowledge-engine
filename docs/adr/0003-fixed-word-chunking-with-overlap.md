# ADR-0003: Fixed-size word chunking with overlap

**Date**: 2026-10-16
**Status**: accepted
**Deciders**: Phone Myint San

## Context

Documents must be split before embedding: one vector can only represent one idea well,
and retrieved pieces must fit the LLM context window. The splitting strategy directly
drives retrieval quality and is the most commonly cited weak point of RAG systems.

## Decision

We split extracted text into 300-word windows that overlap by 50 words, implemented
as a ~10-line pure function (`chunk()` in `app.py`).

## Alternatives Considered

### Alternative 1: Sentence/paragraph-aware splitting
- **Pros**: chunks align with natural meaning boundaries
- **Cons**: needs sentence segmentation (NLTK/spaCy or regex heuristics), more code and more edge cases
- **Why not**: PDF text extraction flattens most structure, so the "natural boundaries" are unreliable to begin with

### Alternative 2: Semantic chunking (embed sentences, split on similarity drops)
- **Pros**: best theoretical chunk quality
- **Cons**: an order of magnitude more compute at index time, significant complexity
- **Why not**: unproven benefit for this corpus; revisit only if retrieval quality disappoints

## Consequences

### Positive
- Trivially testable pure function (see `test_app.py`)
- Overlap guarantees a sentence straddling a boundary survives intact in at least one chunk

### Negative
- Chunks can split tables, lists, or topic boundaries mid-flow
- Word count is a crude proxy for token count

### Risks
- Poor answers on heavily structured documents (tables, forms). First upgrade:
  heading-aware splitting; second: hybrid keyword + vector retrieval.
