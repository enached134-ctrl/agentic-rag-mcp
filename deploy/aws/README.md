# Same RAG, two clouds

This is the grounded-RAG idea from the main server, re-deployed on a **pure-AWS** stack —
so the exact same "cite your source or refuse" behaviour runs behind a serverless endpoint,
with no external vector DB.

| Layer | Railway deploy (main) | AWS deploy (this folder) |
|---|---|---|
| Embeddings | Voyage `voyage-3.5` | **Amazon Titan Text Embeddings V2** (Bedrock) |
| Generation | Anthropic Claude API | **Bedrock Converse** — Amazon Nova by default, Claude drop-in once authorized |
| Vector store | Postgres + pgvector | bundled corpus, in-memory cosine |
| Compute | container on Railway | **AWS Lambda** (arm64) |
| Ingress | streamable HTTP (MCP) | **Lambda Function URL** |
| IaC | `railway.json` | **AWS SAM** (`template.yaml`) |

The corpus is embedded once at cold start and searched in-memory (it's tiny), so the whole
thing is one stateless Lambda — nothing to run between requests, nothing to pay for at idle.

## Deploy

Prereqs: AWS SAM CLI, credentials in the environment, and **Bedrock model access enabled**
for Titan Embeddings V2 + a Claude model (Bedrock console → Model access).

```bash
cd deploy/aws
sam build
sam deploy --guided        # first time: pick region us-east-1, stack name agentic-rag-aws
```

SAM prints the Function URL. Then:

```bash
curl -s -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is groundedness, and what should the system do when the context is missing?"}'
```

```json
{
  "answer": "Groundedness means every claim is supported by the retrieved context [1]. When the context is missing, the system should refuse rather than guess [2].",
  "citations": [{"n": 1, "source": "eval-corpus/groundedness.md"}, ...],
  "backend": "aws-bedrock"
}
```

## Model access notes

The handler talks to models through the **Bedrock Converse API**, which is model-agnostic —
the same code runs Amazon Nova, Anthropic Claude, Llama, etc. Only `LlmModelId` changes.

- **Amazon Nova** (default) and **Titan Embeddings V2** are enabled automatically on any
  account, so this deploys and answers out of the box.
- **Anthropic Claude on Bedrock** requires a one-time account authorization. On brand-new
  accounts AWS gates this behind a support case ("Your account is not authorized…"); once
  granted, set `LlmModelId=us.anthropic.claude-3-5-haiku-20241022-v1:0` — no code change.

## Teardown

```bash
sam delete --stack-name agentic-rag-aws
```
