# ADR-0004: Single-file application

**Date**: 2026-10-16
**Status**: accepted
**Deciders**: Phone Myint San

## Context

FastAPI projects conventionally split into routers, services, schemas, and config
modules. This application has two endpoints, one pure function, and no database
models. The codebase also doubles as a learning artefact, so being readable top to
bottom in one sitting is a feature.

## Decision

The entire backend lives in one file, `app.py` (~160 commented lines), plus a single
static `index.html` for the UI. No build step, no frontend framework.

## Alternatives Considered

### Alternative 1: Layered layout (routers/, services/, schemas/)
- **Pros**: scales to many endpoints, familiar to FastAPI teams
- **Cons**: four files of indirection wrapping ~60 lines of logic
- **Why not**: structure should be earned by size; two endpoints don't earn it

### Alternative 2: React/Vite frontend
- **Pros**: componentised UI, richer interactivity
- **Cons**: node toolchain, build step, dependency tree larger than the whole backend
- **Why not**: the UI is two forms and an answer card; vanilla JS covers it

## Consequences

### Positive
- A reader can trace a request end to end without leaving the file
- Zero frontend tooling; the server ships its own UI via `FileResponse`

### Negative
- The file must be split if endpoints multiply (threshold: roughly when auth or a
  second resource type appears)

### Risks
- None significant at this size.
