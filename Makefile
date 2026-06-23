# Use ">" as the recipe prefix so this works regardless of tab handling.
.RECIPEPREFIX := >
.PHONY: install lint test run schema eval

install:
> pip install -e ".[dev]"

lint:
> ruff check src tests

test:
> pytest -q

run:
> agentic-rag-mcp

schema:
> psql "$$DATABASE_URL" -f sql/schema.sql

eval:
> cd evals && promptfoo eval -c promptfooconfig.yaml
