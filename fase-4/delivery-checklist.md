# Checklist de entrega

## Código e qualidade

- [x] Três serviços independentes, Dockerfiles, manifests e pipelines.
- [x] Cobertura local: OS 97,23% (54 testes), Billing 94,97% (63), Execution 93,65% (48); quality gates aprovados.
- [x] Saga, mensageria, Inbox/Outbox, compensações e BDD versionados.
- [x] Swagger/OpenAPI nativo em cada FastAPI (`/docs`, `/openapi.json`).
- [ ] Criar/push dos repositórios remotos e configurar PR obrigatório/checks.
- [ ] Executar pipelines remotos e anexar artifacts/prints.
- [ ] Autorizar/revisar Terraform plan e deploy AWS.

## PDF

- [ ] Nomes e RM dos participantes.
- [ ] Links dos três serviços, infraestrutura e documentação.
- [ ] Link público/não listado do vídeo.
- [ ] Diagrama geral, limites, Saga, persistência, mensageria e decisões.
- [ ] Evidências de cobertura, CI/CD, Kubernetes e observabilidade.

## Roteiro do vídeo — máximo 15 minutos

1. Contexto, três bounded contexts e diagrama (2 min).
2. Bancos isolados, SQS/ElasticMQ e contratos (2 min).
3. Fluxo feliz completo e Swagger (4 min).
4. Falha, idempotência e compensação da Saga (2 min).
5. Testes, cobertura e quality gates (2 min).
6. Pipeline e deploy de um serviço após gates (2 min).
7. New Relic por `order_id`, `saga_id` e `correlation_id`; limitações (1 min).

Não demonstrar cobrança real nem exibir credenciais/dados pessoais.
