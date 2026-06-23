FROM python:3.12-slim

WORKDIR /app

# Install the package (src layout, hatchling build backend).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Serve over HTTP for hosted deploys (Railway/Fly). Override via env as needed.
ENV RAG_TRANSPORT=http \
    RAG_HTTP_HOST=0.0.0.0 \
    RAG_HTTP_PORT=8000

EXPOSE 8000

CMD ["agentic-rag-mcp"]
