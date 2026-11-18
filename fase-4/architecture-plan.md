# Plano arquitetural aprovado — Fase 4

## Estado

Aprovado em 2026-11-08 como base para o planejamento da implementação. Este documento não substitui o enunciado em `requirements_fase_4.md`; partes planejadas, incluindo a execução local integrada, ainda não foram implementadas.

## Objetivo

Evoluir o monólito da Fase 3 para três microsserviços independentes, preservando regras de negócio e infraestrutura compartilhada, com mensageria assíncrona, Saga Pattern, persistência SQL e NoSQL, pagamento por QR dinâmico do Mercado Pago, testes e deploy Kubernetes independente.

## Decisões aprovadas

1. O pagamento ocorre após a conclusão do reparo e antes da entrega da OS.
2. Um único RDS PostgreSQL hospeda bancos lógicos isolados para OS e Billing, com usuários sem acesso cruzado.
3. O Execution Service usa DynamoDB.
4. A mensageria implantada usa Amazon SQS. ElasticMQ foi considerada para um futuro ambiente local, que ainda não está implementado nem validado.
5. A Saga é orquestrada por um process manager dentro do OS Service, sem quarto microsserviço.
6. O catálogo comercial e os preços pertencem ao Billing Service; diagnóstico, fila, reparo e consumo físico de peças pertencem ao Execution Service.
7. A qualidade é verificada dentro do runner, sem SonarCloud, por um conjunto de ferramentas equivalentes com quality gates bloqueantes.
8. Os serviços são expostos por rotas separadas no API Gateway, reutilizando o EKS e a rede compartilhados.

## Limites dos serviços

### OS Service

- clientes e veículos;
- abertura, consulta, estado global e histórico da OS;
- estado e coordenação da Saga;
- projeções mínimas de orçamento, execução e pagamento;
- integração existente com a Lambda de CPF.

### Billing Service

- catálogo comercial de serviços e preços;
- orçamento e snapshots financeiros;
- aprovação ou recusa;
- criação, consulta, expiração e reembolso de pagamentos;
- adapter e webhook do Mercado Pago.

### Execution Service

- diagnóstico;
- fila de produção;
- tarefas de reparo;
- peças e consumo operacional;
- conclusão da execução.

## Persistência

- `os_db`: PostgreSQL, usuário exclusivo do OS Service.
- `billing_db`: PostgreSQL, usuário exclusivo do Billing Service.
- tabelas DynamoDB específicas do Execution Service.
- nenhum serviço recebe credenciais do banco de outro serviço.
- cada serviço mantém migrations ou bootstrap de persistência independente.
- projeções locais são atualizadas por eventos e não criam autoridade concorrente sobre o dado de origem.

## Mensageria e confiabilidade

- filas SQS standard e DLQ por consumidor na AWS;
- ElasticMQ como implementação local preferencial, por ser compatível com a API SQS e menor que LocalStack;
- Transactional Outbox nos bancos SQL;
- Inbox idempotente em todos os consumidores;
- outbox transacional em DynamoDB usando `TransactWriteItems`;
- entrega pelo menos uma vez, tolerância a duplicatas e eventos fora de ordem;
- envelope versionado com `event_id`, `event_type`, `event_version`, `occurred_at`, `correlation_id`, `causation_id`, `saga_id`, `order_id` e `payload`;
- payloads sem CPF, credenciais ou dados pessoais desnecessários.

## Fluxo da Saga

```text
OS aberta
  -> diagnóstico solicitado
  -> diagnóstico concluído
  -> orçamento solicitado
  -> orçamento gerado
  -> orçamento aprovado
  -> execução solicitada
  -> reparo concluído
  -> pagamento criado
  -> pagamento confirmado
  -> OS entregue
```

Falhas antes do início do reparo podem cancelar a OS e liberar reservas. Reparos iniciados ou concluídos não são revertidos tecnicamente: seguem para tratamento manual auditável. Pagamentos confirmados somente são reembolsados por comando explícito e idempotente.

## Qualidade no runner

Cada pipeline executa, de forma bloqueante:

- Ruff para lint;
- Black para formatação;
- mypy para tipagem;
- Bandit para segurança estática;
- Xenon/Radon para limite de complexidade;
- pytest e pytest-cov com mínimo de 80%;
- validação OpenAPI, manifests Kubernetes e Terraform quando aplicável.

Esse conjunto será registrado em ADR como ferramenta equivalente ao SonarQube, com os resultados preservados como artifacts do workflow.

## Restrições operacionais

- não alterar a tag `fase-3-final`;
- manter `tech-challenge-fiap` como referência histórica;
- não executar push, merge, criação remota de repositório, configuração remota de branch protection ou deploy AWS sem autorização;
- validar permissões SQS e DynamoDB com operações somente leitura antes de qualquer provisionamento;
- todo o fluxo deve ser executável localmente sem credenciais AWS ou Mercado Pago reais.
