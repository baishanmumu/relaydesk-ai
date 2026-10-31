# RelayDesk vectorizer

`vectorizer.app.main` prepares FAQ, travel, and catalog vectors for Qdrant. It reads `OPENAI_API_KEY` or `EMBEDDING_API_KEY`, `QDRANT_URL`, and `SQLITE_DB_PATH` from the environment.

Run from the repository root with `poetry run python -m vectorizer.app.main`. FAQ files belong in `faq_documents/`; local databases and Qdrant storage are not committed.
