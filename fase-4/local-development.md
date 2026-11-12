# Execução local

Requisitos: Docker, Python 3.12 e Poetry 2.2.

```bash
cd architecture-docs/fase-4/test-environment
docker compose up -d

cd ../../../tech-challenge-fiap-os-service
poetry install
poetry run uvicorn src.api.main:app --port 8001
```

Repita para Billing na porta `8002`. Execution é iniciado pela factory/runtime configurada com DynamoDB Local. ElasticMQ, DynamoDB Local, PostgreSQL e fake Mercado Pago estão no compose de testes. Swagger fica em `/docs`, OpenAPI em `/openapi.json` e health check em `/health`.

```bash
cd ../tech-challenge-fiap-execution-service
DYNAMODB_ENDPOINT_URL=http://localhost:8000 poetry run uvicorn src.api.runtime:create_runtime_app --factory --port 8003
```

Validação por serviço:

```bash
poetry run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
bash scripts/quality.sh
```

O BDD completo está em `architecture-docs/fase-4/bdd/` e usa apenas dependências locais.
