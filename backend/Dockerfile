FROM mambaorg/micromamba:1.5.10

USER root
WORKDIR /app

COPY environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml \
    && micromamba clean --all --yes

ENV MAMBA_DOCKERFILE_ACTIVATE=1
ENV PATH="/opt/conda/bin:$PATH"

COPY pyproject.toml uv.lock* ./
COPY app ./app

RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
