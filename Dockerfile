# ===== Stage 1: "builder" installs the libraries =====
# Slim = small Debian image that already has Python 3.12
FROM python:3.12-slim AS builder
WORKDIR /build 

# A virtual environment is one folder holding all installed libraries,
# so we can copy it into the final image in one step
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy ONLY the requirements file first. Docker caches this layer, so the
# slow install reruns only when requirements.txt changes, not on every code edit
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== Stage 2: the final image (small: no pip cache, no build leftovers) =====
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/Harshit-TheCoder/translator"

# Create a normal user. A NUMERIC id (10001) lets Kubernetes verify "not root" later
RUN useradd --uid 10001 --no-create-home appuser
WORKDIR /app 

# Take the finished libraries from stage 1, then our code (changes most often, so last)
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/

# PATH: use the venv's python. UNBUFFERED: logs appear immediately in `docker logs`
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Everything below runs as this user, not root
USER 10001

# Documentation only: the app listens on 8001
EXPOSE 8001

# 0.0.0.0 = accept connections from outside the container (127.0.0.1 would not work)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
