# Observabilidade distribuída

## Objetivo

Cada microsserviço está instrumentado para emitir logs JSON em `stdout`, eventos customizados ao agente New Relic e manter `correlation_id`, `saga_id` e `order_id` durante HTTP, publicação e consumo de mensagens. Logs dos serviços e access logs do API Gateway/CloudWatch foram observados no sandbox. A ingestão no New Relic e a visualização de tracing distribuído ainda não foram verificadas no painel; não as descrevemos como evidência de funcionamento.

## Instrumentação

| Componente | Logs/eventos | Campos principais |
|---|---|---|
| Middleware HTTP | `http.request` / `HttpRequest` | serviço, método, rota, status, duração, correlação |
| SQS publisher | `message.published` / `MessagePublished` | tipo e ID do evento, message ID, correlação e Saga |
| SQS consumer | `message.consumed`, `message.failed` / `MessageConsumed` | tipo e ID do evento, receive count, correlação e Saga |
| Process manager | `saga.transition`, `saga.duplicate` / `SagaTransition` | estado anterior/novo, evento, Saga e OS |
| Mercado Pago | `mercado_pago.request` / `MercadoPagoRequest` | operação, status, tentativa, latência e resultado |

O tracing HTTP do agente New Relic é habilitado ao iniciar o processo com `newrelic-admin run-program`. Os eventos assíncronos carregam os mesmos identificadores no envelope, permitindo relacionar transações separadas por consultas NRQL.

## Segurança

A sanitização é recursiva e substitui por `[REDACTED]` valores associados a `authorization`, `cpf`, `document`, `password`, `qr_payload`, `secret` e `token`. Payloads completos de requisições, mensagens e QR Code não são registrados. Erros usam apenas o tipo da exceção quando podem conter dados externos.

## Configuração

- `NEW_RELIC_LICENSE_KEY`: segredo injetado pelo ambiente; nunca versionado.
- `NEW_RELIC_APP_NAME`: nome individual, por exemplo `oficina-os-service`.
- `NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true`.
- Sem licença, logs JSON e correlação continuam ativos; o envio de eventos torna-se no-op.

As imagens dos serviços iniciam API e workers pelo `newrelic-admin run-program`; essa configuração descreve os workloads implantados, não um passo a passo de execução local.

## Diagnóstico de uma OS

1. Copiar `order_id` ou `correlation_id` da resposta HTTP.
2. Consultar `HttpRequest`, `MessagePublished`, `MessageConsumed` e `SagaTransition` pelas consultas versionadas em `new-relic/queries.md`.
3. Verificar eventos com `receive_count > 1` e mensagens `message.failed` antes de reproduzir DLQ.
4. Para pagamento, correlacionar `MercadoPagoRequest` apenas pelo `correlation_id`/OS; tokens e QR payloads nunca aparecem.

## Dashboards importáveis

Os arquivos [operacionais e da jornada da Saga](new-relic/dashboards/README.md) usam somente os eventos customizados existentes. Eles não adicionam métricas de status da OS ou durações de negócio. A importação na UI não confirma que os eventos estejam chegando: a ingestão precisa ser verificada na conta.

Os testes unitários usam um recorder injetável e não exigem cloud ou licença. Logs permanecem em `stdout` e são coletados pelo ambiente implantado. Ainda não há um ambiente integrado local com Docker Compose/Kind para executar os três serviços juntos. A validação de ingestão no New Relic depende de credencial externa e deve ser feita somente em ambiente autorizado; permanece pendente para a submissão. Veja [current-status.md](current-status.md).
