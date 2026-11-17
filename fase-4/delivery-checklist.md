# Checklist de entrega

## Código e qualidade

- [x] Três serviços independentes, Dockerfiles, manifests e pipelines.
- [x] CI remoto: OS 93,18% (67 testes), Billing 91,34% (84), Execution 86,96% (56); workflows concluídos com sucesso em 17/11/2026. [Evidências e artifacts](current-status.md#pipelines-e-cobertura).
- [x] Saga, mensageria, Inbox/Outbox, compensações e BDD versionados.
- [x] Swagger/OpenAPI nativo em cada FastAPI (`/docs`, `/openapi.json`).
- [x] Repositórios remotos, workflows independentes e regras de proteção de `main` geridas pela organização.
- [x] Executar pipelines remotos; salvar/linkar artifacts como evidência no PDF final.
- [x] Implantação no sandbox e fluxo de compra de teste validados em 17/11; preservar links/logs redigidos no material final.

## PDF

- [ ] Nomes e RM dos participantes.
- [ ] Links dos três serviços, infraestrutura e documentação.
- [ ] Link público/não listado do vídeo.
- [ ] Diagrama geral, limites, Saga, persistência, mensageria e decisões.
- [ ] Evidências de cobertura, CI/CD e Kubernetes; evidência de ingestão New Relic permanece pendente.

## Roteiro do vídeo — máximo 15 minutos

1. Contexto, três bounded contexts e diagrama (2 min).
2. Bancos isolados, SQS/ElasticMQ e contratos (2 min).
3. Fluxo feliz completo e Swagger (4 min).
4. Falha, idempotência e compensação da Saga (2 min).
5. Testes, cobertura e quality gates (2 min).
6. Pipeline e deploy de um serviço após gates (2 min).
7. Logs e correlação observados; apresentar New Relic somente se a ingestão e o tracing forem confirmados (1 min).

Não demonstrar cobrança real nem exibir credenciais/dados pessoais.
