# Golden datasets

A golden dataset is a **fixed set of test questions with expected outcomes**, used to measure
the quality of an AI system the same way unit tests measure the correctness of ordinary code.
It is the single cheapest reliability upgrade available to a team shipping LLM features.

## Size guidance

For a production system, a golden dataset of **50 to 100 cases built from real traffic** is
the practical starting point. It is large enough to catch meaningful regressions and small
enough to run on every change. This repository ships a **seed golden dataset of 20 cases**,
designed to be extended with domain questions from the system's real usage.

## The three case categories

A useful golden dataset always mixes three categories:

1. **Answerable cases** — questions the corpus can answer; the expected outcome is a grounded,
   cited answer.
2. **Refusal cases** — questions the corpus cannot answer; the expected outcome is an explicit
   refusal rather than a fabricated answer.
3. **Adversarial cases** — questions with a false premise or leading phrasing; the expected
   outcome is a correction or refusal, never agreement with the false premise.

## The regression-capture rule

Every time the system fails in production, that failure becomes a new golden case. This is
the regression-capture rule: the dataset grows from real failures, so no bug has to be fixed
twice. A golden dataset that never grows is a sign the team is not looking at its failures.

## Why "you don't know what working means"

If a team cannot write down 50 questions with expected outcomes, it does not yet know what
"working" means for its own system — and no amount of prompt tuning can fix an undefined
target. Writing the golden dataset is often more clarifying than any architecture decision.
