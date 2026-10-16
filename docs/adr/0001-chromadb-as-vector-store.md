# ADR-0001: ChromaDB as the vector store

**Date**: 2026-10-16
**Status**: accepted
**Deciders**: Phone Myint San

## Context

The engine needs to store chunk embeddings and run nearest-neighbour searches over
them. This is a single-user, local-first tool, so operational simplicity matters more
than scale. Whatever we pick must persist across restarts and need zero infrastructure
to run.

## Decision

We use ChromaDB with a `PersistentClient` writing to a local `chroma_db/` directory.

## Alternatives Considered

### Alternative 1: PostgreSQL + pgvector
- **Pros**: real database, SQL filtering alongside vector search, production-ready
- **Cons**: requires a running Postgres instance, migrations, connection management
- **Why not**: too much operational weight for a local single-user tool

### Alternative 2: FAISS
- **Pros**: fastest raw similarity search, battle-tested
- **Cons**: just an index — no persistence layer, no metadata storage, no document store; we would build all of that ourselves
- **Why not**: we would be reimplementing what Chroma already bundles

### Alternative 3: Pinecone / hosted vector DB
- **Pros**: no local resources, scales without effort
- **Cons**: network dependency, cost, sends document content to a third party
- **Why not**: a personal knowledge base should keep its documents on the owner's machine

## Consequences

### Positive
- Zero setup: the store is created on first run, persisted as files
- Embedding function attaches to the collection, so add/query auto-embed
- Metadata (source filename) lives next to the vectors, enabling citations

### Negative
- Not suited to concurrent multi-user access
- Approximate search behaviour and tuning options are limited compared to pgvector/FAISS

### Risks
- If the project ever becomes multi-user, migrate to pgvector; the collection API
  surface we use (add/query with metadata) maps over cleanly.
