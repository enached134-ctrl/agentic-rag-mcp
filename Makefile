# Use ">" as the recipe prefix so this works regardless of tab handling.
.RECIPEPREFIX := >
.PHONY: install lint test run schema seed eval

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

seed:
> python evals/seed.py --schema --reset

eval:
> cd evals && promptfoo eval -c promptfooconfig.yaml
