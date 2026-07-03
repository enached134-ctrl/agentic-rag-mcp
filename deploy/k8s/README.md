# Kubernetes deploy

Minimal, production-shaped manifests for the MCP server over streamable HTTP:
`Deployment` (readiness/liveness probes, resource limits, secrets via `envFrom`) +
`ClusterIP Service` on port 8000.

## Local smoke test (kind)

```bash
# 1. Cluster + image
kind create cluster --name agentic-rag
docker build -t agentic-rag-mcp:local .
kind load docker-image agentic-rag-mcp:local --name agentic-rag

# 2. Secrets (real keys stay out of git — secret.yaml is gitignored)
cp deploy/k8s/secret.example.yaml deploy/k8s/secret.yaml   # edit values
kubectl apply -f deploy/k8s/secret.yaml

# 3. Deploy
kubectl apply -f deploy/k8s/deployment.yaml -f deploy/k8s/service.yaml
kubectl get pods -l app=agentic-rag-mcp --watch

# 4. Reach it
kubectl port-forward svc/agentic-rag-mcp 8000:8000
# MCP endpoint: http://localhost:8000/mcp  (streamable HTTP)
```

The pod becomes `Ready` when the HTTP transport accepts connections; the `ask`/`ingest`
tools additionally need valid `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY` and a reachable
`DATABASE_URL` from the secret.

## Hosted clusters (EKS/GKE/AKS)

Push the image to a registry, point `image:` at it, and provision the secret from your
secret manager instead of a local file. The manifests are intentionally plain YAML —
easy to wrap in Kustomize/Helm when the environment count grows.
