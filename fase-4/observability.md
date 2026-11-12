# Observabilidade distribuída

## Objetivo

Cada microsserviço emite logs JSON em `stdout`, eventos customizados para o agente New Relic e mantém os identificadores `correlation_id`, `saga_id` e `order_id` durante HTTP, publicação e consumo de mensagens. A aplicação continua funcional quando o agente ou a licença New Relic não estiverem configurados.

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

Exemplo de inicialização:

```bash
NEW_RELIC_APP_NAME=oficina-os-service \
newrelic-admin run-program uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

## Diagnóstico de uma OS

1. Copiar `order_id` ou `correlation_id` da resposta HTTP.
2. Consultar `HttpRequest`, `MessagePublished`, `MessageConsumed` e `SagaTransition` pelas consultas versionadas em `new-relic/queries.md`.
3. Verificar eventos com `receive_count > 1` e mensagens `message.failed` antes de reproduzir DLQ.
4. Para pagamento, correlacionar `MercadoPagoRequest` apenas pelo `correlation_id`/OS; tokens e QR payloads nunca aparecem.

## Execução local

Os testes usam um recorder injetável e não exigem cloud ou licença. Logs permanecem em `stdout` e podem ser coletados pelo Docker Compose ou pelo runner CI. A validação de ingestão no New Relic depende de credencial externa e deve ser feita somente em ambiente autorizado.
