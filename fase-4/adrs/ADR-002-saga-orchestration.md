# ADR-002 — Saga orquestrada pelo OS Service

## Estado

Aceita em 2026-11-08.

## Contexto

O ciclo da OS atravessa diagnóstico, orçamento, aprovação, execução e pagamento. Não existe transação ACID entre os bancos e algumas ações, como reparo físico ou pagamento confirmado, não podem ser simplesmente desfeitas.

## Decisão

Implementar um process manager persistente dentro do OS Service. Ele mantém o estado da Saga, consome eventos e publica comandos por mensageria. Não será criado um microsserviço orquestrador separado.

Fluxo aprovado:

1. abrir OS;
2. solicitar e concluir diagnóstico;
3. solicitar e gerar orçamento;
4. aguardar aprovação;
5. solicitar e concluir execução;
6. criar e confirmar pagamento;
7. entregar a OS.

O pagamento ocorre depois do reparo e antes da entrega.

Recusa do orçamento e falha/cancelamento da execução antes do reparo cancelam a OS automaticamente. Depois do início do reparo, falhas seguem para pendência manual auditável; a intervenção não desfaz o reparo físico. Pagamento rejeitado ou reembolsado também exige tratamento manual no OS Service. Esses caminhos não equivalem a compensação automática em todas as etapas exigida literalmente pelo enunciado; são uma limitação atual, mantida explícita em [known-limitations.md](../known-limitations.md).

## Alternativas consideradas

### Coreografia completa

Rejeitada como estratégia principal porque espalharia a lógica do fluxo e das compensações pelos três serviços, reduzindo clareza, observabilidade e demonstrabilidade.

### Orquestrador como quarto microsserviço

Rejeitada porque adicionaria operação, banco e pipeline sem uma responsabilidade independente além da própria OS.

### Chamadas REST síncronas encadeadas

Rejeitada porque acopla disponibilidade e não resolve publicação atômica, retries ou transações longas.

## Consequências

- o OS Service conhece a sequência do processo, não as regras internas dos participantes;
- estado da Saga e comando de saída são gravados atomicamente por Outbox;
- consumidores usam Inbox idempotente;
- falhas e compensações ficam visíveis por `saga_id`;
- ações irreversíveis não recebem rollback fictício; o estado passa para intervenção manual;
- o deploy de cada serviço é iniciado por `workflow_dispatch` como gate de release, e a pipeline automatiza as etapas posteriores.

## Requisitos relacionados

REQ-SAGA-001 a REQ-SAGA-004, REQ-COMM-002 e DEC-001/DEC-005.
