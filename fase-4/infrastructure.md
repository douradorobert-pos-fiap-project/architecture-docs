# Infraestrutura

`shared-infra` preserva VPC, EKS, NLB, API Gateway e observabilidade da Fase 3 e acrescenta três ECRs imutáveis, rotas por contexto, filas SQS/DLQ opcionais e tabela DynamoDB opcional. `database-infra` preserva um RDS PostgreSQL e oferece bootstrap idempotente de dois bancos lógicos e usuários isolados.

SQS e DynamoDB ficam desabilitados por padrão até a confirmação das permissões do sandbox. O resultado atual está em [aws-sandbox-validation.md](aws-sandbox-validation.md). Não foram executados `terraform apply`, deploy AWS ou alteração remota.

Cada serviço possui Dockerfile, Deployment, Service, HPA, ConfigMap e Secret de exemplo; OS e Billing também possuem Job de migration. Recursos compartilhados permanecem em `shared-infra`; workloads permanecem em seus repositórios.
