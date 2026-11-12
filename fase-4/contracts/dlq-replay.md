# Replay de DLQ

As filas usam entrega pelo menos uma vez e encaminham mensagens para a DLQ após três recebimentos sem confirmação.

Antes do replay:

1. identifique e corrija a causa da falha;
2. valide a mensagem contra `events/integration-event.schema.json`;
3. preserve `event_id`, `correlation_id`, `causation_id` e `saga_id`;
4. reenvie para a fila de origem;
5. remova a mensagem da DLQ somente depois que o serviço confirmar o processamento.

Preservar `event_id` garante que o Inbox descarte com segurança uma mensagem já processada. Eventos fora de ordem devem permanecer disponíveis até que sua precondição seja satisfeita ou até análise manual; não devem ser alterados para forçar uma transição inválida.
