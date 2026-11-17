# Tech Challenge FIAP — Fase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar três microsserviços independentes para o ciclo completo de uma ordem de serviço, coordenados por Saga e mensageria, com pagamento Mercado Pago, execução local, Kubernetes, CI/CD e observabilidade distribuída.

**Status da execução local:** O ambiente integrado com Compose/Kind descrito nas Tasks 8 e 15 ainda não foi aplicado. Essas etapas continuam pendentes; não há runbook de execução local disponível até que a stack seja implementada e validada.

**Architecture:** O OS Service mantém a identidade da OS e orquestra a Saga; Billing mantém orçamento, aprovação e pagamento; Execution mantém diagnóstico e reparo. Comandos e eventos trafegam por SQS/ElasticMQ com Outbox e Inbox; OS e Billing usam bancos PostgreSQL lógicos isolados no mesmo RDS e Execution usa DynamoDB.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, boto3, DynamoDB, SQS/ElasticMQ, pytest, pytest-bdd, Ruff, Black, mypy, Bandit, Xenon/Radon, Docker, Kubernetes, Terraform, GitHub Actions e New Relic.

**Spec:** `architecture-docs/fase-4/architecture-plan.md` e `architecture-docs/fase-4/requirements_fase_4.md`

## Global Constraints

- Preservar as quatro tags `fase-3-final` e não modificar o monólito sem nova autorização específica.
- Não fazer push, merge, deploy AWS, criação remota de repositório ou alteração de branch protection sem autorização.
- Não acessar diretamente o banco de outro serviço.
- Manter cobertura mínima individual de 80%.
- Usar pelo menos PostgreSQL e DynamoDB.
- Executar a análise de qualidade dentro do runner, sem SonarCloud.
- Não depender da AWS ou de credenciais Mercado Pago para testes locais.
- Propagar `correlation_id`, `causation_id`, `saga_id` e `order_id` em HTTP, mensagens e logs.
- Não registrar CPF, tokens, chaves, QR payload completo ou credenciais.
- Todo consumidor deve ser idempotente e tolerar entrega duplicada.

## Review Focus

- Mensagem duplicada deve produzir uma única mudança de estado e uma única chamada externa.
- Evento atrasado ou fora de ordem deve ser ignorado ou rejeitado sem regredir o estado da OS.
- Pagamento confirmado nunca pode entregar a OS antes da conclusão do reparo.
- Reparos já iniciados não podem ser tratados como rollback técnico; devem gerar pendência manual auditável.
- Indisponibilidade de SQS, DynamoDB ou Mercado Pago deve preservar o estado local e permitir retry seguro.

---

## Estrutura de arquivos planejada

### `tech-challenge-fiap-os-service`

- `src/domain/`: OS, estado da Saga, histórico e regras de transição.
- `src/application/`: comandos, consultas e process manager.
- `src/infrastructure/database/`: SQLAlchemy, Alembic, Outbox e Inbox.
- `src/infrastructure/messaging/`: publisher SQS, relay e consumers.
- `src/infrastructure/observability/`: logs, métricas e tracing.
- `src/api/`: clientes, veículos, OS e health checks.

### `tech-challenge-fiap-billing-service`

- `src/domain/`: catálogo, orçamento, aprovação e pagamento.
- `src/application/`: geração de orçamento, aprovação, pagamento e reembolso.
- `src/infrastructure/database/`: PostgreSQL, Outbox e Inbox.
- `src/infrastructure/mercado_pago/`: porta, adapter HTTP e validação de callback.
- `src/infrastructure/messaging/`: consumidores e publisher.
- `src/api/`: orçamento, aprovação, pagamento e webhook.

### `tech-challenge-fiap-execution-service`

- `src/domain/`: diagnóstico, fila, reparo, peças e transições.
- `src/application/`: iniciar/concluir diagnóstico e execução.
- `src/infrastructure/database/`: repositories e transações DynamoDB.
- `src/infrastructure/messaging/`: consumidores, publisher e inbox/outbox.
- `src/api/`: consultas e comandos operacionais.

### Compartilhado sem pacote de runtime

Contratos de evento serão documentados em `architecture-docs/fase-4/contracts/events/` e copiados/testados em cada consumidor. Não será criado um pacote Python compartilhado que acople os ciclos de release dos serviços.

---

### Task 1: Baseline, ADRs e validação das decisões

**Files:**
- Create: `architecture-docs/fase-4/requirements-traceability.md`
- Create: `architecture-docs/fase-4/adrs/ADR-001-service-boundaries.md`
- Create: `architecture-docs/fase-4/adrs/ADR-002-saga-orchestration.md`
- Create: `architecture-docs/fase-4/adrs/ADR-003-persistence.md`
- Create: `architecture-docs/fase-4/adrs/ADR-004-sqs-and-local-broker.md`
- Create: `architecture-docs/fase-4/adrs/ADR-005-runner-quality-gates.md`
- Create: `architecture-docs/fase-4/diagrams/target-architecture.mmd`
- Create: `architecture-docs/fase-4/diagrams/saga-sequence.mmd`

**Interfaces:**
- Consumes: requisitos e plano arquitetural aprovados.
- Produces: decisões estáveis e IDs de requisito usados por todos os repositórios.

- [ ] **Step 1: Registrar a matriz requisito → serviço → teste → evidência**

- [ ] **Step 2: Escrever os cinco ADRs com contexto, alternativas, decisão e consequências**

- [ ] **Step 3: Criar os diagramas Mermaid da arquitetura e da Saga**

- [ ] **Step 4: Validar referências e sintaxe Mermaid**

Run: `if rg -n 'TBD|TODO|FIXME' architecture-docs/fase-4/requirements-traceability.md architecture-docs/fase-4/adrs architecture-docs/fase-4/diagrams; then exit 1; fi` e, em seguida, renderizar os dois arquivos em `architecture-docs/fase-4/diagrams/` com `mmdc`.

Expected: nenhum requisito indefinido e renderização sem erro.

- [ ] **Step 5: Commit**

```bash
git add fase-4
git commit -m "docs: define fase 4 distributed architecture"
```

### Task 2: Criar os três repositórios locais e o contrato comum

**Files:**
- Create: `tech-challenge-fiap-os-service/pyproject.toml`
- Create: `tech-challenge-fiap-billing-service/pyproject.toml`
- Create: `tech-challenge-fiap-execution-service/pyproject.toml`
- Create: `<service>/src/infrastructure/messaging/envelope.py`
- Create: `<service>/tests/unit/infrastructure/test_event_envelope.py`
- Create: `architecture-docs/fase-4/contracts/events/envelope.schema.json`

**Interfaces:**
- Consumes: envelope definido no plano arquitetural.
- Produces: `EventEnvelopeV1` com serialização JSON idêntica nos três serviços.

- [ ] **Step 1: Criar branches ou repositórios Git somente locais, sem remotes**

- [ ] **Step 2: Escrever teste parametrizado do envelope nos três serviços**

Assertions: UUIDs válidos; timestamp UTC; `event_version == 1`; rejeição de campos obrigatórios ausentes; round-trip JSON.

- [ ] **Step 3: Executar os testes e confirmar falha por módulo inexistente**

Run: `poetry run pytest tests/unit/infrastructure/test_event_envelope.py -v`

Expected: FAIL por `EventEnvelopeV1` ausente.

- [ ] **Step 4: Implementar `EventEnvelopeV1` e o JSON Schema versionado**

- [ ] **Step 5: Executar testes, lint e schema validation**

Expected: PASS nos três repositórios.

- [ ] **Step 6: Commit independente em cada repositório**

### Task 3: Implementar o núcleo do OS Service

**Files:**
- Create: `tech-challenge-fiap-os-service/src/domain/service_order.py`
- Create: `tech-challenge-fiap-os-service/src/domain/service_order_status.py`
- Create: `tech-challenge-fiap-os-service/src/domain/saga.py`
- Create: `tech-challenge-fiap-os-service/src/application/open_service_order.py`
- Create: `tech-challenge-fiap-os-service/src/application/process_saga_event.py`
- Create: `tech-challenge-fiap-os-service/tests/unit/domain/test_service_order.py`
- Create: `tech-challenge-fiap-os-service/tests/unit/application/test_saga_process_manager.py`

**Interfaces:**
- Consumes: `EventEnvelopeV1`.
- Produces: `open_order(...) -> ServiceOrder`, `handle_event(envelope) -> list[PendingCommand]`.

- [ ] **Step 1: Escrever testes da máquina de estados e invariantes**

Cobrir abertura, diagnóstico, orçamento, aprovação, execução, pagamento, entrega, cancelamento e rejeição de transição inválida.

- [ ] **Step 2: Executar e confirmar falha dos testes**

- [ ] **Step 3: Portar apenas regras válidas do monólito e introduzir os estados distribuídos**

- [ ] **Step 4: Escrever testes do process manager, inclusive evento duplicado e fora de ordem**

- [ ] **Step 5: Implementar geração determinística dos comandos da Saga**

- [ ] **Step 6: Executar cobertura do domínio/aplicação**

Run: `poetry run pytest tests/unit --cov=src/domain --cov=src/application --cov-fail-under=80`

Expected: PASS e cobertura ≥80%.

- [ ] **Step 7: Commit**

### Task 4: Persistência, API e Outbox do OS Service

**Files:**
- Create: `tech-challenge-fiap-os-service/migrations/versions/001_initial.py`
- Create: `tech-challenge-fiap-os-service/src/infrastructure/database/models.py`
- Create: `tech-challenge-fiap-os-service/src/infrastructure/database/repositories.py`
- Create: `tech-challenge-fiap-os-service/src/infrastructure/database/outbox.py`
- Create: `tech-challenge-fiap-os-service/src/infrastructure/database/inbox.py`
- Create: `tech-challenge-fiap-os-service/src/api/main.py`
- Create: `tech-challenge-fiap-os-service/src/api/routes/*.py`
- Create: `tech-challenge-fiap-os-service/tests/integration/test_os_api.py`
- Create: `tech-challenge-fiap-os-service/tests/integration/test_outbox_atomicity.py`

**Interfaces:**
- Consumes: casos de uso da Task 3.
- Produces: REST de clientes, veículos e OS; tabelas `service_orders`, `service_order_history`, `sagas`, `outbox_messages`, `inbox_messages`.

- [ ] **Step 1: Escrever testes de repository, API e atomicidade estado+outbox**

- [ ] **Step 2: Confirmar falha antes da implementação**

- [ ] **Step 3: Implementar migrations e repositories sem acesso aos bancos Billing/Execution**

- [ ] **Step 4: Implementar endpoints e propagação de `X-Correlation-ID`**

- [ ] **Step 5: Validar OpenAPI, migrations e suite**

- [ ] **Step 6: Commit**

### Task 5: Implementar o Billing Service

**Files:**
- Create: `tech-challenge-fiap-billing-service/src/domain/catalog.py`
- Create: `tech-challenge-fiap-billing-service/src/domain/quote.py`
- Create: `tech-challenge-fiap-billing-service/src/domain/payment.py`
- Create: `tech-challenge-fiap-billing-service/src/application/generate_quote.py`
- Create: `tech-challenge-fiap-billing-service/src/application/approve_quote.py`
- Create: `tech-challenge-fiap-billing-service/migrations/versions/001_initial.py`
- Create: `tech-challenge-fiap-billing-service/tests/unit/domain/test_quote.py`
- Create: `tech-challenge-fiap-billing-service/tests/integration/test_billing_api.py`

**Interfaces:**
- Consumes: `DiagnosisCompletedV1`, `QuoteGenerationRequestedV1`, `PaymentCreationRequestedV1`.
- Produces: `QuoteGeneratedV1`, `QuoteApprovedV1`, `QuoteRejectedV1`, eventos de pagamento.

- [ ] **Step 1: Escrever testes de cálculo com `Decimal`, snapshots e aprovação idempotente**

- [ ] **Step 2: Confirmar falha**

- [ ] **Step 3: Portar catálogo/cálculo do monólito e separar ownership financeiro**

- [ ] **Step 4: Implementar PostgreSQL, Inbox e Outbox transacionais**

- [ ] **Step 5: Implementar API e testes de contrato**

- [ ] **Step 6: Executar cobertura ≥80% e commit**

### Task 6: Integrar Mercado Pago no Billing Service

**Files:**
- Create: `tech-challenge-fiap-billing-service/src/application/ports/payment_gateway.py`
- Create: `tech-challenge-fiap-billing-service/src/infrastructure/mercado_pago/client.py`
- Create: `tech-challenge-fiap-billing-service/src/infrastructure/mercado_pago/webhook.py`
- Create: `tech-challenge-fiap-billing-service/src/api/routes/webhooks.py`
- Create: `tech-challenge-fiap-billing-service/tests/contract/test_mercado_pago_client.py`
- Create: `tech-challenge-fiap-billing-service/tests/integration/test_payment_webhook.py`

**Interfaces:**
- Consumes: pagamento interno e credenciais por ambiente.
- Produces: `create_dynamic_qr(payment) -> PaymentGatewayResult`, `get_payment_status(external_id) -> PaymentStatus`, `refund(external_id, amount) -> RefundResult`.

- [ ] **Step 1: Escrever contract tests com servidor HTTP falso**

Cobrir `X-Idempotency-Key`, timeout, 429/5xx, resposta inválida, QR dinâmico e ausência de credenciais.

- [ ] **Step 2: Implementar a porta e o adapter sem SDK obrigatório**

- [ ] **Step 3: Escrever testes de webhook duplicado, assinatura quando aplicável e confirmação ativa pela API**

- [ ] **Step 4: Implementar webhook como sinal, nunca como fonte única de verdade**

- [ ] **Step 5: Testar que `live_mode=true` é recusado em ambiente de teste**

- [ ] **Step 6: Executar suite e commit**

### Task 7: Implementar o Execution Service em DynamoDB

**Files:**
- Create: `tech-challenge-fiap-execution-service/src/domain/execution.py`
- Create: `tech-challenge-fiap-execution-service/src/application/diagnose.py`
- Create: `tech-challenge-fiap-execution-service/src/application/execute_repair.py`
- Create: `tech-challenge-fiap-execution-service/src/infrastructure/database/dynamodb_repository.py`
- Create: `tech-challenge-fiap-execution-service/src/infrastructure/database/bootstrap.py`
- Create: `tech-challenge-fiap-execution-service/tests/unit/domain/test_execution.py`
- Create: `tech-challenge-fiap-execution-service/tests/integration/test_dynamodb_repository.py`

**Interfaces:**
- Consumes: `DiagnosisRequestedV1`, `ExecutionRequestedV1`, compensações antes do reparo.
- Produces: `DiagnosisCompletedV1`, `ExecutionStartedV1`, `ExecutionCompletedV1`, `ExecutionFailedV1`.

- [ ] **Step 1: Escrever testes das transições e da regra de irreversibilidade do reparo iniciado**

- [ ] **Step 2: Escrever testes DynamoDB Local para condition expressions e duplicatas**

- [ ] **Step 3: Implementar agregado e repository com `TransactWriteItems`**

- [ ] **Step 4: Implementar Inbox/Outbox na mesma transação DynamoDB**

- [ ] **Step 5: Implementar API operacional e testes**

- [ ] **Step 6: Executar cobertura ≥80% e commit**

### Task 8: Ligar SQS/ElasticMQ, retries e DLQs

**Files:**
- Create: `<service>/src/infrastructure/messaging/sqs_client.py`
- Create: `<service>/src/infrastructure/messaging/outbox_relay.py`
- Create: `<service>/src/infrastructure/messaging/consumer.py`
- Create: `<service>/tests/integration/test_messaging.py`
- Create: `architecture-docs/fase-4/contracts/events/*.schema.json`
- Create: `architecture-docs/fase-4/contracts/asyncapi.yaml`

**Interfaces:**
- Consumes: outboxes e handlers das Tasks 4, 5 e 7.
- Produces: publicação pelo menos uma vez, deduplicação por Inbox e replay de DLQ documentado.

- [ ] **Step 1: Escrever testes integrados contra ElasticMQ**

Cobrir sucesso, duplicata, indisponibilidade, retry, poison message, DLQ e evento fora de ordem.

- [ ] **Step 2: Implementar cliente SQS configurável por endpoint**

- [ ] **Step 3: Implementar relay com lease e retry exponencial**

- [ ] **Step 4: Implementar consumers que confirmam mensagem somente após commit**

- [ ] **Step 5: Validar todos os schemas e AsyncAPI**

- [ ] **Step 6: Executar suites e commits independentes**

### Task 9: Implementar o BDD ponta a ponta

**Files:**
- Create: `architecture-docs/fase-4/test-environment/docker-compose.yml`
- Create: `architecture-docs/fase-4/bdd/features/service_order_saga.feature`
- Create: `architecture-docs/fase-4/bdd/steps/test_service_order_saga.py`
- Create: `architecture-docs/fase-4/bdd/fakes/mercado_pago.py`

**Interfaces:**
- Consumes: imagens e APIs dos três serviços.
- Produces: evidência automatizada do fluxo real distribuído.

- [ ] **Step 1: Escrever cenário feliz completo**

Abrir OS, concluir diagnóstico, gerar/aprovar orçamento, executar, confirmar pagamento e entregar.

- [ ] **Step 2: Escrever cenário de falha antes da execução com compensação**

- [ ] **Step 3: Escrever cenário de duplicidade de `PaymentConfirmed`**

- [ ] **Step 4: Subir PostgreSQL, DynamoDB Local, ElasticMQ e fake Mercado Pago**

- [ ] **Step 5: Executar `pytest-bdd` e coletar logs correlacionados**

Expected: três cenários PASS e uma única entrega/pagamento por OS.

- [ ] **Step 6: Commit**

### Task 10: Observabilidade distribuída

**Files:**
- Create: `<service>/src/infrastructure/observability/logging.py`
- Create: `<service>/src/infrastructure/observability/telemetry.py`
- Create: `<service>/tests/unit/infrastructure/test_observability.py`
- Create: `architecture-docs/fase-4/observability.md`
- Create: `architecture-docs/fase-4/new-relic/queries.md`

**Interfaces:**
- Consumes: IDs do envelope e headers HTTP.
- Produces: logs JSON, traces e eventos sem dados sensíveis.

- [ ] **Step 1: Escrever testes de propagação e sanitização**

- [ ] **Step 2: Adaptar a instrumentação New Relic da Fase 3**

- [ ] **Step 3: Instrumentar HTTP, publish, consume, Saga e Mercado Pago**

- [ ] **Step 4: Documentar NRQL para OS, DLQ, Saga e latência**

- [ ] **Step 5: Executar testes e commits**

### Task 11: Quality gates e pipelines independentes

**Files:**
- Create: `<service>/.github/workflows/pipeline.yml`
- Modify: `<service>/pyproject.toml`
- Create: `<service>/scripts/quality.sh`
- Create: `<service>/tests/architecture/test_boundaries.py`

**Interfaces:**
- Consumes: suites dos serviços.
- Produces: checks bloqueantes executados no runner e artifacts de cobertura/qualidade.

- [ ] **Step 1: Configurar Ruff, Black, mypy, Bandit e Xenon/Radon com limites explícitos**

- [ ] **Step 2: Escrever teste de arquitetura que proíbe imports e credenciais entre serviços**

- [ ] **Step 3: Criar job PR: dependências, qualidade, testes, cobertura e Docker build**

- [ ] **Step 4: Criar jobs main: ECR e deploy, condicionados ao sucesso completo**

- [ ] **Step 5: Validar YAML e executar `scripts/quality.sh` localmente**

- [ ] **Step 6: Preservar relatórios como artifacts e commit**

### Task 12: Kubernetes de cada serviço

**Files:**
- Create: `<service>/k8s/deployment.yaml`
- Create: `<service>/k8s/service.yaml`
- Create: `<service>/k8s/configmap.yaml`
- Create: `<service>/k8s/hpa.yaml`
- Create: `<sql-service>/k8s/migration-job.yaml`
- Create: `<service>/k8s/secret.example.yaml`

**Interfaces:**
- Consumes: imagens e configurações por serviço.
- Produces: deploy independente no namespace `oficina` com secrets separados.

- [ ] **Step 1: Criar testes estáticos dos manifests**

Validar probes, requests/limits, non-root, imagem imutável e ausência de secrets reais.

- [ ] **Step 2: Criar manifests e Jobs de migration isolados**

- [ ] **Step 3: Validar com renderização e schema Kubernetes**

- [ ] **Step 4: Fazer smoke test local em cluster somente se já disponível**

- [ ] **Step 5: Commit por serviço**

### Task 13: Adaptar Terraform compartilhado e de banco

**Files:**
- Modify: `shared-infra/terraform/ecr.tf`
- Create: `shared-infra/terraform/messaging.tf`
- Create: `shared-infra/terraform/dynamodb.tf`
- Modify: `shared-infra/terraform/api_gateway.tf`
- Modify: `shared-infra/terraform/networking.tf`
- Modify: `shared-infra/terraform/outputs.tf`
- Modify: `database-infra/terraform/main.tf`
- Modify: `database-infra/terraform/outputs.tf`
- Create: `shared-infra/tests/test_fase4_static.py`
- Create: `database-infra/tests/test_database_isolation.py`

**Interfaces:**
- Consumes: nomes de filas, tabelas, serviços e rotas.
- Produces: três ECRs, SQS/DLQ, DynamoDB, rotas e dois bancos lógicos isolados.

- [ ] **Step 1: Comparar `shared-infra` HEAD com `fase-3-final` e preservar mudanças posteriores intencionais**

- [ ] **Step 2: Escrever testes Terraform antes dos recursos**

- [ ] **Step 3: Implementar recursos com variáveis de habilitação para o Sandbox**

- [ ] **Step 4: Implementar bootstrap idempotente dos bancos lógicos e usuários**

- [ ] **Step 5: Executar `terraform fmt`, `init -backend=false`, `validate` e testes estáticos**

- [ ] **Step 6: Gerar `terraform plan` somente com placeholders e sem aplicar**

- [ ] **Step 7: Commit; não executar `apply`**

### Task 14: Validar permissões do AWS Academy Sandbox

**Files:**
- Create: `architecture-docs/fase-4/aws-sandbox-validation.md`
- Create: `shared-infra/scripts/check-fase4-permissions.sh`

**Interfaces:**
- Consumes: credenciais temporárias fornecidas externamente.
- Produces: relatório de capacidade SQS/DynamoDB/ECR/EKS sem provisionamento.

- [ ] **Step 1: Implementar script somente leitura com `get-caller-identity`, list/describe permitidos**

- [ ] **Step 2: Validar sintaxe e comportamento sem credenciais**

- [ ] **Step 3: Solicitar autorização antes de consultar a AWS**

- [ ] **Step 4: Registrar permissões encontradas e fallback**

Fallback: manter SQS como arquitetura-alvo; demonstração local usa ElasticMQ. Se SQS for proibido, documentar RabbitMQ no EKS apenas após nova decisão arquitetural aprovada.

- [ ] **Step 5: Commit**

### Task 15: Documentação e evidências finais

**Files:**
- Create: `architecture-docs/fase-4/architecture.md`
- Create: `architecture-docs/fase-4/infrastructure.md`
- Create: `architecture-docs/fase-4/saga.md`
- Create: `architecture-docs/fase-4/local-development.md`
- Create: `architecture-docs/fase-4/deployment.md`
- Create: `architecture-docs/fase-4/known-limitations.md`
- Create: `architecture-docs/fase-4/delivery-checklist.md`
- Modify: `<service>/README.md`

**Interfaces:**
- Consumes: implementação e resultados reais das Tasks 1–14.
- Produces: documentação, Swagger/Postman, evidências e roteiro verificável do vídeo/PDF.

- [ ] **Step 1: Atualizar matriz de rastreabilidade com links para testes e workflows**

- [ ] **Step 2: Documentar execução local e implantação sem afirmar recursos não provisionados**

- [ ] **Step 3: Exportar OpenAPI e criar collection Postman quando útil**

- [ ] **Step 4: Registrar cobertura e quality gates por serviço**

- [ ] **Step 5: Criar roteiro do vídeo de até quinze minutos**

- [ ] **Step 6: Criar checklist do PDF e itens que dependem de participantes/links remotos**

- [ ] **Step 7: Executar verificação final completa e commit**

---

## Gates de conclusão por etapa

Uma etapa só pode ser marcada como concluída quando:

1. seus testes falharam antes da implementação relevante e passam depois;
2. cobertura individual permanece em pelo menos 80%;
3. quality gates locais passam;
4. contratos e documentação estão sincronizados;
5. `git diff --check` não encontra erros;
6. nenhuma credencial ou dado pessoal foi introduzido;
7. alterações externas ou deploys continuam pendentes de autorização explícita.

## Ordem recomendada de execução

Executar Tasks 1–4 primeiro para estabelecer contratos e o coordenador. Depois executar Billing e Execution (Tasks 5–7), integração distribuída e BDD (Tasks 8–9), observabilidade/entrega (Tasks 10–12), infraestrutura e validação do Sandbox (Tasks 13–14) e documentação final (Task 15).

Cada task deve produzir um commit local revisável. Os novos repositórios não recebem remote nem push até autorização.
