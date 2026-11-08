# ADR-004 — Amazon SQS com ElasticMQ local

## Estado

Aceita em 2026-11-08, condicionada à validação das permissões do AWS Academy Sandbox.

## Contexto

A solução precisa de mensageria real no fluxo de negócio, retries, tolerância a duplicatas, DLQs e execução local sem dependência contínua da AWS.

## Decisão

Usar filas Amazon SQS Standard e DLQs na AWS. Em desenvolvimento, CI e BDD, usar ElasticMQ por implementar a API SQS e permitir o mesmo adapter boto3 com endpoint configurável.

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

Aceitável, mas ElasticMQ é preferido para mensageria isolada por ser menor e suficiente. DynamoDB Local cobre o segundo serviço emulado.

## Consequências

- duplicatas e reordenação são comportamentos esperados e testados;
- cada fila tem DLQ, visibility timeout e política de retry explícitos;
- o código muda endpoint/configuração, não implementação, entre local e AWS;
- fan-out adicional exigirá filas separadas ou SNS em decisão futura;
- a demonstração local independe de credenciais temporárias.

## Requisitos relacionados

REQ-COMM-002/003, REQ-SAGA-001/002, REQ-INFRA-002 e DEC-004.
