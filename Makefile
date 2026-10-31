.PHONY: help qdrant web vectorize down

help:
	@echo "make qdrant     Start the local vector database"
	@echo "make web        Start the FastAPI browser workspace"
	@echo "make vectorize  Index FAQ and configured business data"
	@echo "make down       Stop local Docker services"

qdrant:
	docker compose up -d qdrant

web:
	poetry run uvicorn web_app.app.main:app --reload --host 127.0.0.1 --port 8000

vectorize:
	poetry run python -m vectorizer.app.main

down:
	docker compose down

.DEFAULT_GOAL := help
