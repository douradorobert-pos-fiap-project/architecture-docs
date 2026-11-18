# Dashboards importáveis do New Relic

Os arquivos JSON desta pasta podem ser importados em **New Relic → Dashboards → Import dashboard**. O fluxo oficial permite colar o JSON e selecionar a conta e as permissões na importação. Veja a [documentação de importação/exportação](https://docs.newrelic.com/docs/query-your-data/explore-query-data/dashboards/dashboards-charts-import-export-data/).

As consultas usam `accountId: 0` como marcador neutro. Se a interface não substituir esse valor ao selecionar a conta, substitua todos os zeros pelo ID numérico da sua conta New Relic antes de importar. Os dashboards são privados (`PRIVATE`).

## Arquivos

- `operacao-microsservicos.json`: tráfego HTTP, latência, respostas 5xx, mensagens e chamadas Mercado Pago observadas.
- `jornada-saga.json`: atividade agregada por estado/evento da Saga, volume das rotas de OS/Billing e respostas Mercado Pago registradas.

## Limites dos dados atuais

- `HttpRequest` contém `service`, `path`, `status_code` e `duration_ms`, então permite separar tráfego HTTP por serviço.
- `MessagePublished` e `MessageConsumed` não incluem o nome do serviço; esses gráficos agregam os três microsserviços.
- `SagaTransition` não inclui IDs da OS/Saga nem o serviço. O painel mostra contagem de transições, não OS únicas nem status e histórico de negócio por OS.
- `MercadoPagoRequest` só é enviado no caminho de resposta bem-sucedida do client; sua ausência de eventos de erro não significa ausência de falhas.
- Os eventos customizados emitidos pelos workers são chamados fora de uma transação HTTP e atualmente o helper não passa um objeto `application` ao agente. A [API Python do New Relic](https://docs.newrelic.com/docs/apm/agents/python-agent/python-agent-api/recordcustomevent-python-agent-api/) documenta esse parâmetro para eventos fora de transação; verifique se esses tipos aparecem na conta antes de confiar nos widgets correspondentes.
- A ingestão no New Relic ainda não foi confirmada. Os widgets podem ficar vazios até que o agente envie eventos para a conta escolhida.

Não houve alterações nos serviços nem deploys para produzir estes dashboards. As definições consultam apenas os tipos de evento implementados. Consulte [observabilidade e limitações](../observability.md) e as [consultas NRQL existentes](../queries.md).
