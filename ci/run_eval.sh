#!/usr/bin/env bash
# Stop on the first error (-e), on unset variables (-u), and inside pipes.
set -euo pipefail

# Point the real API at the FAKE LLM, never at a real model.
export LLM_BASE_URL="http://127.0.0.1:9999"
export LLM_MODEL="stub-model"
# Redis runs on this machine (GitHub service container / Jenkins redis-server).
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
# Tracing off: no collector exists in CI.
unset OTEL_EXPORTER_OTLP_ENDPOINT || true

# Start the fake LLM and the API in the background.
python evals/stub_llm.py &
STUB_PID=$!
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
APP_PID=$!

# Always stop both background programs when this script ends.
trap 'kill $STUB_PID $APP_PID 2>/dev/null || true' EXIT

# Wait up to 30 seconds for /health to answer.
for _ in $(seq 1 30); do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" 2>/dev/null; then
    break
  fi
  sleep 1
done

# Run the scoring. Its exit code becomes this script's exit code.
EVAL_BASE_URL="http://127.0.0.1:8000" python evals/run_eval.py