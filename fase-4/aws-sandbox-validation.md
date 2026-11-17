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

## Evidência operacional mais recente

Em 2026-11-17, uma consulta AWS somente leitura confirmou o cluster EKS `oficina-sandbox` como `ACTIVE`. Os Deployments de API de OS, Billing e Execution estavam com `2/2` réplicas disponíveis; os três workers, com `1/1` prontos. A rota pública de webhook do API Gateway também estava configurada para encaminhar ao ALB interno pelo VPC Link.

Além da inspeção de infraestrutura, uma compra de teste de R$ 1,00 percorreu os serviços: Billing registrou `APPROVED`, a notificação Mercado Pago do tipo `order` recebeu HTTP `200` e a OS terminou em `DELIVERED`. Os detalhes operacionais e limites dessa evidência estão em [current-status.md](current-status.md).

Essa evidência demonstra recursos ativos e um caminho funcional naquele momento; não comprova duração/ disponibilidade futura do sandbox nem permissões para criar ou alterar recursos. O resultado histórico do auditor em 12/11 foi inconclusivo e não deve ser tratado como status atual.

## Decisão e fallback

- SQS é a mensageria da implantação; ElasticMQ é usada no desenvolvimento local.
- DynamoDB é o banco NoSQL do Execution Service; DynamoDB Local é usado no desenvolvimento local.
- Desenvolvimento, testes integrados, BDD e CI usam ElasticMQ e DynamoDB Local, sem dependência contínua da AWS.
- Se SQS estiver proibido, a substituição por RabbitMQ no EKS exige nova decisão arquitetural aprovada; não haverá fallback silencioso em produção.
- Recursos já ativos no sandbox não significam autorização para provisionar novos recursos. Qualquer mudança de infraestrutura requer `terraform plan` revisado e autorização apropriada.

## Limitações

- As credenciais do Academy são temporárias; o resultado representa apenas a sessão e o momento consultados.
- Operações `list`/`describe` não comprovam permissões de criação, alteração ou exclusão.
- O auditor não consulta políticas IAM e não tenta contornar restrições do sandbox.
