# OlympiadSimplified

OlympiadSimplified transforms competitive-exam questions into clear, interactive learning experiences.

## Monorepo layout

- `apps/question-extractor` — PNG → validated question JSON → Markdown using local Gemma and LangGraph.
- `packages` — future shared schemas and libraries.
- `docs` — product and architecture documentation.
- `samples` — non-sensitive sample inputs and expected outputs.

## Current application

See [`apps/question-extractor/README.md`](apps/question-extractor/README.md) to run the first proof of concept.
