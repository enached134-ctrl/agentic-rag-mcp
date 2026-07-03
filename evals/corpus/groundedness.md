# Groundedness

Groundedness is the property that **every claim in a generated answer is supported by the
retrieved context**. A RAG system is grounded when nothing in its output goes beyond what the
source chunks actually say.

## The failure mode that matters most

The most damaging failure mode of a RAG system is the **confident wrong answer**: retrieval
returns weak or irrelevant chunks, and the model answers fluently anyway. Users forgive an
honest "I don't know". They do not forgive confident nonsense, because it destroys trust in
every future answer — including the correct ones.

## The refusal principle

When the retrieved context does not contain the information needed to answer, **the correct
output is a refusal**: the system should say plainly that the available sources do not cover
the question, and ideally state what evidence would be needed. In a well-designed RAG system,
refusal is a feature, not a bug. An agent that cannot refuse is not trustworthy.

## Citations

A citation is an explicit link from a claim to the exact source chunk that supports it. In
this project, answers cite sources with bracketed numbers such as `[1]` or `[2]`, where each
number refers to a numbered context item. The contract is simple: **grounded or refuse** —
every sentence carries its evidence, or the answer is withheld.

## How groundedness is checked here

This repository checks groundedness in two complementary ways:

1. A **self-critique agent** reviews every draft against the retrieved context before the
   answer is returned; unsupported drafts are sent back for revision.
2. An **evaluation suite** scores groundedness, citation presence, and refusal correctness on
   a golden dataset, so a regression is caught before it reaches a user.
