# LLM-as-judge

LLM-as-judge is an evaluation technique in which **a language model grades outputs against a
written rubric**. It is the practical way to score dimensions that have no exact string match
— groundedness, faithfulness to sources, refusal correctness, tone.

## When to use a judge, and when not to

Use an LLM judge for **subjective or semantic dimensions**: "is every claim supported by the
context?", "did the answer admit uncertainty instead of fabricating?". Do **not** use a judge
where a deterministic assertion works: citation-marker presence, output format, latency
thresholds, or exact values. Deterministic checks are cheaper, faster, and never drift.

## Calibration

A judge is only as trustworthy as its calibration. The standard practice is to **spot-check
judge verdicts against human labels** on a sample of cases, and to rewrite the rubric until
judge–human agreement is high. A rubric that a human reviewer would apply inconsistently will
be applied inconsistently by the judge too.

## Judge model choice

The judge should be a **separate, typically cheaper model** than the system under test.
Grading is a simpler task than generation, and using a distinct model avoids the system
grading its own homework with its own biases.

## The pairing rule

The reliable pattern is **deterministic assertions plus rubric grading together**: hard
checks catch format and contract violations at zero cost, while the judge scores the semantic
qualities that matter. In this repository, the eval suite pairs a citation-presence check and
a latency threshold (deterministic) with rubric-graded groundedness and refusal correctness
(LLM-as-judge).
