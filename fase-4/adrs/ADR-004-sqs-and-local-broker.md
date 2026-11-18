# ADR-004 — Amazon SQS e alternativa local futura

## Estado

Aceita em 2026-11-08 para a mensageria implantada na AWS. A alternativa local descrita aqui ainda não está implementada nem validada.

## Contexto

A solução precisa de mensageria real no fluxo de negócio, retries, tolerância a duplicatas e DLQs. Um ambiente local completo seria útil, mas ainda não está disponível.

## Decisão

Usar filas Amazon SQS Standard e DLQs na AWS. ElasticMQ permanece como alternativa escolhida para uma futura execução local, por implementar a API SQS e permitir o mesmo adapter boto3 com endpoint configurável. Ela não é usada pelo BDD atual nem por um ambiente integrado local.

Cada mensagem usa envelope versionado e cada consumidor possui sua fila. Publicação parte de Transactional Outbox; consumo usa Inbox idempotente. A semântica assumida é entrega pelo menos uma vez.

Antes de criar recursos AWS, um script somente leitura verificará identidade e permissões disponíveis. Se SQS não for permitido, a mudança para RabbitMQ no EKS exigirá nova decisão aprovada; não haverá fallback silencioso em produção.

## Alternativas consideradas

### RabbitMQ no EKS

Viável e portátil, mas rejeitado como primeira escolha porque exige broker stateful, volume, atualização, monitoramento e recuperação operados pela equipe.

### Amazon MQ

Rejeitado por custo, tempo de provisionamento e provável incompatibilidade com o Sandbox.

### Kafka/MSK

Rejeitado por complexidade e escala desproporcionais ao problema.

### LocalStack

Aceitável, mas ElasticMQ é a alternativa futura preferida para mensageria isolada por ser menor e suficiente. O BDD atual não usa broker emulado.

## Consequências

- duplicatas e reordenação são comportamentos esperados e cobertos por testes com mocks;
- cada fila tem DLQ, visibility timeout e política de retry explícitos;
- a meta para o futuro é trocar endpoint/configuração, sem alterar o adapter, entre ElasticMQ e AWS;
- fan-out adicional exigirá filas separadas ou SNS em decisão futura;
- a execução local integrada permanece pendente e não deve ser demonstrada como capacidade disponível.

## Requisitos relacionados

REQ-COMM-002/003, REQ-SAGA-001/002, REQ-INFRA-002 e DEC-004.
