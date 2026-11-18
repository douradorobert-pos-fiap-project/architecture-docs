# Consultas New Relic (NRQL)

Substitua os valores de exemplo sem incluir CPF, token ou QR payload.

## Linha do tempo de uma ordem

```sql
FROM HttpRequest, MessagePublished, MessageConsumed, SagaTransition, MercadoPagoRequest
SELECT * WHERE order_id = 'ORDER_UUID' SINCE 24 hours ago
```

## Transições e falhas da Saga

```sql
FROM SagaTransition
SELECT count(*) FACET previous_state, current_state, event_type
WHERE service = 'os-service' SINCE 1 day ago
```

```sql
FROM Log
SELECT count(*) FACET error_type
WHERE event = 'message.failed' OR event = 'saga.failed'
SINCE 1 day ago
```

## Duplicidade, retry e DLQ

```sql
FROM MessageConsumed
SELECT count(*) FACET event_type
WHERE receive_count > 1 SINCE 1 day ago
```

```sql
FROM Log
SELECT count(*) FACET service, event_type
WHERE event = 'message.failed' AND receive_count >= 3
SINCE 1 day ago
```

## Latência HTTP por serviço

```sql
FROM HttpRequest
SELECT percentile(duration_ms, 50, 95, 99), average(duration_ms)
FACET service, path SINCE 1 hour ago
```

## Integração Mercado Pago

```sql
FROM MercadoPagoRequest
SELECT count(*), percentage(count(*), WHERE status_code >= 400), percentile(duration_ms, 95)
FACET method, path SINCE 1 day ago
```
