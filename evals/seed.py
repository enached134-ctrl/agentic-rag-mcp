"""Seed the vector store with the eval corpus (evals/corpus/*.md).

Usage:
    python evals/seed.py --schema --reset

--schema  apply sql/schema.sql first (idempotent; needs pgvector available)
--reset   delete previously seeded corpus rows before ingesting
"""

from __future__ import annotations

import argparse
import pathlib
import sys

EVALS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parent
CORPUS_DIR = EVALS_DIR / "corpus"
SOURCE_PREFIX = "eval-corpus/"


def apply_schema() -> None:
    import psycopg

    from agentic_rag_mcp.config import settings

    sql = (REPO_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    # Strip comment lines FIRST, then split — otherwise a statement whose chunk starts
    # with a leading `-- comment` line (e.g. `create extension vector`) is dropped whole.
    body = "\n".join(ln for ln in sql.splitlines() if not ln.strip().startswith("--"))
    statements = [s.strip() for s in body.split(";") if s.strip()]
    with psycopg.connect(settings.database_url) as conn:
        for stmt in statements:
            conn.execute(stmt)
        conn.commit()
    print(f"schema applied ({len(statements)} statements)")


def reset_corpus() -> None:
    import psycopg

    from agentic_rag_mcp.config import settings

    with psycopg.connect(settings.database_url) as conn:
        cur = conn.execute(
            "DELETE FROM documents WHERE source LIKE %s", (SOURCE_PREFIX + "%",)
        )
        conn.commit()
        print(f"reset: {cur.rowcount} old corpus rows deleted")


def seed() -> int:
    # Chunk every corpus file, then embed + insert the whole corpus in ONE request
    # (Voyage's free tier allows only 3 requests/minute — one call per file rate-limits).
    from agentic_rag_mcp import store
    from agentic_rag_mcp.ingest import chunk_text

    items: list[tuple[str, str]] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        source = f"{SOURCE_PREFIX}{path.name}"
        for chunk in chunk_text(path.read_text(encoding="utf-8")):
            items.append((chunk, source))
    total = store.add_documents(items)
    n_files = len(list(CORPUS_DIR.glob("*.md")))
    print(f"ingested {n_files} files as {total} chunks (1 embed request)")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", action="store_true", help="apply sql/schema.sql first")
    parser.add_argument("--reset", action="store_true", help="delete previous corpus rows")
    args = parser.parse_args()

    if args.schema:
        apply_schema()
    if args.reset:
        reset_corpus()
    total = seed()
    if total == 0:
        print("ERROR: no chunks ingested", file=sys.stderr)
        sys.exit(1)
    print(f"done: {total} chunks in the store")


if __name__ == "__main__":
    main()
