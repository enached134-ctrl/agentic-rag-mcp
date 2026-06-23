# Evals

Quality is measured with [promptfoo](https://promptfoo.dev), not asserted.

```bash
pip install -e ".[dev]"          # from the repo root
promptfoo eval -c promptfooconfig.yaml
promptfoo view                   # open the results UI
```

- `provider.py` routes each prompt through the real `ask` pipeline.
- `promptfooconfig.yaml` checks **citation presence**, **faithfulness** (llm-rubric), and
  **latency**.
- Requires env (`ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `DATABASE_URL`) and an ingested corpus.
  The `llm-rubric` grader needs `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.

Add your own domain questions with known-good answers as test cases and track the pass rate /
score over time — that score is what you put on the portfolio.
