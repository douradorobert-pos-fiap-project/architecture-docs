# Arquitetura — Tech Challenge FIAP

Documentação arquitetural do Tech Challenge da pós-graduação em Arquitetura de Software da FIAP.

O conteúdo desta documentação é derivado do código preservado em releases. Ele descreve o que pode ser comprovado nos repositórios e não afirma que os ambientes AWS continuem ativos.

## Fases documentadas

### Fase 3 — Monólito em Kubernetes na AWS

- [Arquitetura da solução](fase-3/architecture.md)
- [Diagrama principal em Mermaid](fase-3/architecture.mmd)
- [Integrações e contratos](fase-3/integrations.md)
- [Infraestrutura, Kubernetes, CI/CD e observabilidade](fase-3/infrastructure.md)
- [Releases e commits analisados](fase-3/releases.md)
- [Diagramas complementares](fase-3/diagrams/)

### Fase 4 — Microsserviços e Saga

- [Arquitetura e limites dos serviços](fase-4/architecture.md)
- [Diagrama de arquitetura](fase-4/diagrams/target-architecture.mmd)
- [Estratégia e compensações da Saga](fase-4/saga.md)
- [Infraestrutura e implantação](fase-4/infrastructure.md) e [deploy manual](fase-4/deployment.md)
- [Validação atual do sandbox](fase-4/current-status.md)
- [Matriz de rastreabilidade dos requisitos](fase-4/requirements-traceability.md)
- [Checklist de entrega](fase-4/delivery-checklist.md)

O código e o fluxo de pagamento foram validados no sandbox em 17/11/2026. As regras de proteção de `main` são geridas no nível da organização. A submissão acadêmica permanece em preparação: faltam o vídeo e o PDF final com participantes e evidências.

## Escopo

A Fase 3 é formada por quatro repositórios:

| Repositório | Responsabilidade |
|---|---|
| `tech-challenge-fiap` | API Python/FastAPI, domínio, persistência, container e manifests Kubernetes |
| `shared-infra` | VPC, EKS, entrada HTTP, ECR, secrets e observabilidade compartilhada |
| `database-infra` | RDS PostgreSQL e sua integração com a rede compartilhada |
| `tech-challenge-fiap-lambda` | Lambda de validação algorítmica de CPF |

Todo o material da Fase 3 considera exclusivamente a tag `fase-3-final` registrada em [releases.md](fase-3/releases.md).
