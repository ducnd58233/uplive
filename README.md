# uplive

Run from the repository root unless a section says otherwise.

## Docker

```bash
docker compose -f deployments/docker/docker-compose.yml up --build
docker compose -f deployments/docker/docker-compose.yml down -v
```

Backend only (redis, api, worker):

```bash
docker compose -f backend/deployments/docker/docker-compose.yml up --build
docker compose -f backend/deployments/docker/docker-compose.yml down -v
```

Redis only:

```bash
docker compose -f backend/deployments/docker/docker-compose.infra.yml up
docker compose -f backend/deployments/docker/docker-compose.infra.yml down -v
```

Frontend only (requires backend network; use `full` profile when defined):

```bash
docker compose -f frontend/deployments/docker/docker-compose.yml --profile full up --build
docker compose -f frontend/deployments/docker/docker-compose.yml down -v
```

Validate compose files:

```bash
docker compose -f deployments/docker/docker-compose.yml config
```

## Local (without Docker)

### Backend

From `./backend`:

```bash
conda env create -f environment.yml
conda activate uplive
uv sync
```

Start Redis locally (or use the Redis compose file above), then:

```bash
uvicorn app.main:app --reload --port 8000
```

Worker (separate terminal, Redis must be running):

```bash
arq app.worker.WorkerSettings
```

Tests and lint:

```bash
pytest
ruff check . && ruff format .
```

### Frontend

From `./frontend` (when the Vite app is present):

```bash
npm install
npm run dev
npm run build
npm run lint
npm test
```
