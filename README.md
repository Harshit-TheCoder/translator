# Translator API

FastAPI translation API that uses Redis for caching and Ollama for local model
inference. Docker Compose also starts Prometheus, Grafana, Loki, Tempo, and
OpenTelemetry Collector for monitoring.

## Run locally

```sh
docker compose up -d --build
curl -sS -X POST http://localhost:8001/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"Good evening, my friend","target_lang":"Spanish"}'
```

Grafana is at http://localhost:3001 and Prometheus is at
http://localhost:9091. Grafana's default local login is `admin` / `admin` unless
`GRAFANA_PASSWORD` is set.

## Kubernetes and Argo CD

The Helm chart is in `helm/translator`. The Argo CD Application and environment
values are kept in the separate `translator-config` repository.

The CI workflow pushes the image to GitHub Container Registry (GHCR). GHCR
packages start private. For a private package, create a Kubernetes pull secret
in the `translator` namespace and set `image.pullSecrets` in the config repo's
values file. To let a cluster pull without a secret, make the GHCR package
public in its package settings.

## Tests

```sh
python -m pytest -q
```
