# ADR-0002: Local embeddings, remote generation

**Date**: 2026-10-16
**Status**: accepted
**Deciders**: Phone Myint San

## Context

A RAG pipeline calls an embedding model many times (every chunk of every document,
plus every query) but a generation model only once per question. Embedding via a paid
API makes cost scale with library size; generation quality, however, is hard to match
locally.

## Decision

Embeddings run locally with Sentence Transformers (`all-MiniLM-L6-v2`, 384 dimensions).
Only the final answer generation calls the OpenAI API (`gpt-4o-mini`).

## Alternatives Considered

### Alternative 1: OpenAI embeddings (`text-embedding-3-small`)
- **Pros**: higher retrieval quality, no local model download, 1536 dims
- **Cons**: every upload and every question costs money and requires network; document content leaves the machine at index time
- **Why not**: indexing a large personal library should be free and offline

### Alternative 2: Fully local generation (llama.cpp / Ollama)
- **Pros**: no API key, fully private end to end
- **Cons**: needs a capable local model, slower answers, more setup for anyone cloning the repo
- **Why not**: out of scope for v1; the OpenAI call is isolated in one place and easy to swap

## Consequences

### Positive
- Indexing is free, offline, and private — only retrieved snippets are ever sent to the API
- One clear seam (`OpenAI().chat.completions.create`) to swap providers later

### Negative
- First run downloads the embedding model (~90 MB) and pulls in PyTorch
- MiniLM retrieval quality trails the large hosted embedding models

### Risks
- Changing the embedding model later invalidates the existing index — every stored
  vector must be re-embedded. Mitigation: wipe `chroma_db/` and re-upload.
