# ADR-003 — Persistência independente com PostgreSQL e DynamoDB

## Estado

Aceita em 2026-11-08.

## Contexto

A Fase 4 exige banco próprio por serviço e o uso combinado de SQL e NoSQL. O AWS Academy Sandbox possui recursos e permissões limitados, tornando três instâncias gerenciadas caras e frágeis.

## Decisão

- OS Service usa o banco lógico PostgreSQL `os_db`.
- Billing Service usa o banco lógico PostgreSQL `billing_db`.
- Execution Service usa tabelas DynamoDB próprias.
- `os_db` e `billing_db` compartilham uma instância RDS, mas possuem usuários, credenciais, migrations e permissões isolados.
- nenhum serviço recebe secret ou permissão para o banco de outro.
- Testes isolados podem usar Moto ou DynamoDB Local; o ambiente integrado local dos três serviços ainda não foi implementado.

## Alternativas consideradas

### Uma instância RDS por serviço SQL

Arquiteturalmente válida, mas rejeitada para o Sandbox por custo, tempo de provisionamento e maior probabilidade de indisponibilidade. Pode ser adotada futuramente sem alterar ownership ou migrations.

### Um schema PostgreSQL compartilhado

Rejeitada porque facilita joins e FKs cruzadas e enfraquece a independência exigida.

### PostgreSQL para os três serviços

Rejeitada por não cumprir o requisito NoSQL e por modelar fila/histórico operacional sem aproveitar acesso por chave e atualização condicional do DynamoDB.

### MongoDB/DocumentDB

Rejeitada porque DocumentDB aumenta custo e complexidade; MongoDB adicionaria outra operação no Kubernetes sem vantagem suficiente sobre DynamoDB e mocks/emuladores usados nos testes isolados.

## Consequências

- migrations independentes para OS e Billing;
- bootstrap idempotente cria bancos e usuários no RDS;
- ausência de FKs e joins entre serviços;
- integridade entre contextos por eventos, snapshots e idempotência;
- Execution usa `TransactWriteItems` e condition expressions para estado, Inbox e Outbox;
- permissões DynamoDB precisam ser verificadas antes do provisionamento AWS.

## Requisitos relacionados

REQ-DATA-001 a REQ-DATA-004 e DEC-002/DEC-003.
