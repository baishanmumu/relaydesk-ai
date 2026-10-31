# Base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry files
COPY pyproject.toml poetry.lock* /app/

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code and the synthetic demo FAQ
COPY relaydesk /app/relaydesk
COPY web_app /app/web_app
COPY vectorizer /app/vectorizer
COPY faq_extension /app/faq_extension
COPY faq_config.yaml /app/faq_config.yaml
COPY faq_documents /app/faq_documents
COPY setup_database.py /app/setup_database.py
COPY init_database.sql /app/init_database.sql

# Set environment variables
ENV PYTHONPATH="/app"

# FastAPI browser workspace
EXPOSE 8000

CMD ["uvicorn", "web_app.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
