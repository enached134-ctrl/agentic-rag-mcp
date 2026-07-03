# Evals

Quality is measured with [promptfoo](https://promptfoo.dev), not asserted — and the gate
runs **in CI on every push**: a regression fails the build like a broken unit test.

## Layout

| Piece | What it is |
|---|---|
| `corpus/*.md` | Self-contained knowledge base the golden dataset is written against |
| `golden.yaml` | **Seed golden dataset — 20 cases**: answerable (grounded + cited), refusal (out-of-corpus), adversarial (false premise) |
| `provider.py` | promptfoo provider routing every question through the real `ask` pipeline (planner → retrieve → synthesize → self-critique) |
| `promptfooconfig.yaml` | Scored dimensions: **citation presence**, **groundedness** (LLM-as-judge), **refusal correctness** (LLM-as-judge), **latency** |
| `seed.py` | Applies the schema and ingests `corpus/` into the pgvector store |

## Run locally

```bash
pip install -e ".[dev]"                 # from the repo root
python evals/seed.py --schema --reset   # seed the corpus (needs DATABASE_URL + VOYAGE_API_KEY)
make eval                               # promptfoo eval
promptfoo view                          # results UI
```

Env required: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `DATABASE_URL`. The `llm-rubric` grader
is pinned to a **separate, cheaper model** than the pipeline (a judge should not be the
system grading its own homework).

## In CI

The `evals` job in `.github/workflows/ci.yml` spins up a `pgvector/pgvector:pg16` service
container, seeds it with this corpus, and runs the golden dataset through the real pipeline.
Nothing is mocked. If the repository secrets (`ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`) are
absent — e.g. on forks — the job skips with a visible notice instead of failing spuriously.

## Extending the dataset (the regression-capture rule)

Every real-world failure becomes a new case in `golden.yaml`, so no bug gets fixed twice.
Add your own domain questions with known-good outcomes and track the pass rate over time —
that score is the number you put on a portfolio.
