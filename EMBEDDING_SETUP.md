# Embedding configuration

The vectorizer reads credentials from environment variables; keep live keys in a local `.env` file and never commit them.

- `EMBEDDING_API_KEY`: optional key for a separate embedding provider; falls back to `OPENAI_API_KEY`.
- `EMBEDDING_BASE_URL`: optional compatible API base URL.
- `USE_LOCAL_EMBEDDINGS=true`: use the configured local model instead of a hosted API.
- `QDRANT_URL` and `QDRANT_KEY`: vector database connection settings.

Copy `.env.example` to `.env`, fill in the needed values, start Qdrant, and run `poetry run python -m vectorizer.app.main` from the repository root.
