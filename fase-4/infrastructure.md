# Infraestrutura

`shared-infra` preserva a VPC, EKS, balanceamento e API Gateway e fornece recursos compartilhados para os serviços. O API Gateway encaminha rotas por contexto através de VPC Link ao ALB interno. A implantação usa filas SQS/DLQ e DynamoDB para Execution. `database-infra` fornece PostgreSQL com bancos lógicos separados para OS e Billing e usuários isolados.

O estado do sandbox e o escopo das verificações estão em [aws-sandbox-validation.md](aws-sandbox-validation.md) e [current-status.md](current-status.md). Em 17/11/2026 o EKS estava ativo e os workloads reportavam réplicas prontas. Este documento não afirma que o estado permanecerá ativo depois dessa observação.

Cada serviço mantém Dockerfile e manifests de Kubernetes; OS e Billing também possuem Job de migration. Recursos compartilhados permanecem em `shared-infra`; workloads permanecem em seus repositórios. O deploy é iniciado manualmente por `workflow_dispatch`, conforme [deployment.md](deployment.md).
