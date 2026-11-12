# Validação de permissões do AWS Academy Sandbox

## Objetivo

Verificar, sem provisionar ou modificar recursos, se a sessão temporária do AWS Academy permite consultar SQS, DynamoDB, ECR e EKS. O resultado orienta a habilitação das variáveis Terraform da Fase 4; ele não substitui um `terraform plan` e nunca autoriza `apply`.

## Auditor somente leitura

O script `shared-infra/scripts/check-fase4-permissions.sh` executa exclusivamente:

- `sts get-caller-identity`;
- `sqs list-queues`;
- `dynamodb list-tables`;
- `ecr describe-repositories`;
- `eks list-clusters`.

Ele exige `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e `AWS_SESSION_TOKEN` já presentes no ambiente, não grava credenciais e não imprime seus valores. A região padrão é `us-east-1`, substituível por `AWS_REGION` ou `AWS_DEFAULT_REGION`.

```bash
cd shared-infra
scripts/check-fase4-permissions.sh
```

Cada capacidade é classificada como `ALLOWED` ou `DENIED_OR_UNAVAILABLE`. A segunda classificação inclui tanto ausência de permissão quanto indisponibilidade/expiração da sessão, pois o auditor evita expor detalhes potencialmente sensíveis retornados pela AWS CLI.

## Resultado da sessão atual

Status em 2026-11-12: **inconclusivo — identidade AWS indisponível**.

A consulta somente leitura foi autorizada e executada, mas `sts get-caller-identity` retornou `DENIED_OR_UNAVAILABLE`. Isso indica credenciais expiradas/inválidas ou ausência da permissão básica na sessão atual. O auditor encerrou nesse ponto e não consultou SQS, DynamoDB, ECR ou EKS; consequentemente, suas permissões permanecem **não confirmadas**.

As validações locais confirmam que o script possui sintaxe Bash válida, falha de forma segura quando não há credenciais e classifica respostas permitidas/negadas usando uma AWS CLI simulada. Nenhuma operação de escrita foi executada.

## Decisão e fallback

- SQS continua sendo a mensageria-alvo na AWS, mas `enable_messaging` permanece `false` até uma sessão confirmar a capacidade.
- DynamoDB continua sendo o banco do Execution Service, mas `enable_execution_dynamodb` permanece `false` até a confirmação.
- Desenvolvimento, testes integrados, BDD e CI usam ElasticMQ e DynamoDB Local, sem dependência contínua da AWS.
- Se SQS estiver proibido, a substituição por RabbitMQ no EKS exige nova decisão arquitetural aprovada; não haverá fallback silencioso em produção.
- Um resultado `ALLOWED` é evidência de consulta, não garantia de permissão para criação. Qualquer provisionamento continua condicionado a autorização explícita e a um `terraform plan` revisado.

## Limitações

- As credenciais do Academy são temporárias; o resultado representa apenas a sessão e o momento consultados.
- Operações `list`/`describe` não comprovam permissões de criação, alteração ou exclusão.
- O auditor não consulta políticas IAM e não tenta contornar restrições do sandbox.
