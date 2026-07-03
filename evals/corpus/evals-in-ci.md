# Evals in CI

Running evaluations in continuous integration means the eval suite executes **on every push,
exactly like unit tests** — and a quality regression fails the build the same way a broken
test does. This turns prompt and pipeline changes from guesses into experiments.

## Why the gate matters

Nobody merges backend code without tests, yet many teams ship prompt changes to
nondeterministic systems with no measurement at all. A prompt edit can silently break tool
selection, citation behaviour, or refusal behaviour. With evals in CI, that regression is
visible in the build **minutes after the commit**, not days later in front of users.

## What this repository scores in CI

The CI eval gate for this project scores four dimensions on the golden dataset:

1. **Citation presence** — answers must reference numbered context items like `[1]`.
2. **Groundedness** — an LLM judge checks every claim against the retrieved context.
3. **Refusal correctness** — out-of-corpus questions must produce an explicit refusal.
4. **Latency** — each pipeline run must finish within the configured threshold.

## The toolchain

Evals here run on **promptfoo**, with a Python provider that routes every test question
through the real multi-agent pipeline — planner, retriever, synthesizer, and self-critique —
against a real pgvector store seeded with this corpus. Nothing is mocked: the eval exercises
the same code path a production question takes.

## The skip gate

In continuous integration, the eval job checks for the required API keys and **skips with a
visible notice when they are absent** (for example on forks), instead of failing spuriously.
On the main repository with secrets configured, the gate is always on: a groundedness or
refusal regression fails the build before it can ship.
