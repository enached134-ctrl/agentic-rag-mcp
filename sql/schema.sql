-- Agentic RAG MCP — vector store schema (Postgres + pgvector).
-- Run once against your Supabase database (SQL editor or psql).
-- Embedding dimension 1024 matches Voyage `voyage-3.5`.

create extension if not exists vector;

create table if not exists documents (
    id          uuid primary key default gen_random_uuid(),
    content     text        not null,
    embedding   vector(1024) not null,
    source      text,
    metadata    jsonb       not null default '{}'::jsonb,
    created_at  timestamptz not null default now()
);

-- Approximate nearest-neighbour index for cosine distance.
create index if not exists documents_embedding_idx
    on documents
    using hnsw (embedding vector_cosine_ops);

create index if not exists documents_source_idx on documents (source);
