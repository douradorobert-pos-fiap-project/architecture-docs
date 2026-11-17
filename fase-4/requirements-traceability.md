# Matriz de rastreabilidade — Fase 4

## Convenções

- **Fonte:** seção do enunciado em `requirements_fase_4.md`.
- **Componente:** autoridade responsável pela implementação ou evidência.
- **Teste/evidência:** prova objetiva esperada; o caminho definitivo será atualizado quando o artefato existir.
- **Estado:** `planejado`, `implementado`, `validado` ou `dependência externa`.

Esta matriz separa requisitos obrigatórios do enunciado de decisões arquiteturais aprovadas. Uma decisão não reduz o requisito original.

## Situação consolidada em 2026-11-17

Esta tabela é a leitura atual dos requisitos. As tabelas detalhadas abaixo preservam o mapeamento original e podem conter estados de planejamento da época em que foram escritos; use esta consolidação como estado vigente.

| Estado atual | Requisitos | Evidência objetiva |
|---|---|---|
| Implementado e validado em sandbox | REQ-ARCH-001 a 003, REQ-DATA-001 a 004, REQ-OS-001 a 003, REQ-BILL-001 a 004, REQ-EXEC-001 a 003, REQ-COMM-001 a 003 | três serviços implantados; APIs/workers prontos; uma compra de teste concluiu com Billing `APPROVED`, webhook `order` HTTP 200 e OS `DELIVERED`. Não implica validação de todos os cenários. |
| Implementado; cenário BDD versionado | REQ-SAGA-001 a 004 | process manager, compensações e BDD presentes. O cenário usa APIs e fake de pagamento e injeta algumas transições diretamente; não valida transporte SQS real. Vídeo ainda pendente. |
| Validado em CI | REQ-QUAL-001 a 004, REQ-CICD-001 a 004 | OS: 67 testes/93,18%; Billing: 84/91,34%; Execution: 56/86,96%. [Runs e detalhes](current-status.md#pipelines-e-cobertura). |
| Pipeline de deploy executada | REQ-CICD-005, REQ-INFRA-001, REQ-INFRA-002 | workflows manuais bem-sucedidos e EKS ativo no momento da observação. Deploy começa por decisão via `workflow_dispatch`. |
| Parcial / pendente externa | REQ-CICD-006 | branch protection e checks obrigatórios em `main` ainda serão configurados pelo responsável. |
| Instrumentado; evidência remota pendente | REQ-OBS-001, REQ-VIDEO-005 | logs observados no CloudWatch; New Relic configurado, mas ingestão e tracing no painel não verificados. |
| Implementado; publicação de evidências pendente | REQ-DELIV-001 a 006 | repositórios, Dockerfiles, manifests, workflows, READMEs e OpenAPI existem; links/artifacts devem ser incluídos na entrega final. |
| Pendente | REQ-VIDEO-001 a 005, REQ-PDF-001 a 003 | vídeo pela equipe, identificação dos participantes e PDF final com links/evidências/diagrama. |
| Documentado | REQ-PDF-004, REQ-PDF-005 | ADRs e documentos de arquitetura da Fase 4. |

Não há evidência de que todos os requisitos estejam integralmente validados. Em particular, compensações automáticas após início do reparo e para pagamento recusado/reembolsado não estão implementadas; nesses casos há intervenção manual. Consulte [current-status.md](current-status.md) e [ADR-002](adrs/ADR-002-saga-orchestration.md).

## Arquitetura e dados

| ID | Requisito obrigatório | Fonte | Componente | Teste/evidência planejada | Estado |
|---|---|---|---|---|---|
| REQ-ARCH-001 | Existirem no mínimo três microsserviços independentes | Separação em Microsserviços | OS, Billing, Execution | três repositórios, três imagens e três APIs implantáveis separadamente | planejado |
| REQ-ARCH-002 | Cada microsserviço possuir repositório próprio | Separação / Infraestrutura | Organização GitHub | URLs e histórico Git dos três repositórios | dependência externa |
| REQ-ARCH-003 | Cada microsserviço possuir infraestrutura própria | Separação / Infraestrutura | cada serviço e `shared-infra` | manifests/pipeline específicos e recursos compartilhados explicitamente separados | planejado |
| REQ-DATA-001 | Cada microsserviço possuir banco próprio | Separação em Microsserviços | OS, Billing, Execution | credenciais isoladas; teste impedindo acesso cruzado | planejado |
| REQ-DATA-002 | Usar ao menos um banco SQL | Separação em Microsserviços | OS e Billing | migrations PostgreSQL e testes de repository | planejado |
| REQ-DATA-003 | Usar ao menos um banco NoSQL | Separação em Microsserviços | Execution | repository e testes com DynamoDB Local | planejado |
| REQ-DATA-004 | Nenhum serviço acessar diretamente o banco de outro | Comunicação | todos | teste arquitetural, secrets isolados e revisão Terraform | planejado |
| REQ-OS-001 | Abrir ordem de serviço | Exemplo OS Service | OS | teste unitário e API `POST /service-orders` | planejado |
| REQ-OS-002 | Atualizar status da OS | Exemplo OS Service | OS/Saga | testes da máquina de estados e eventos | planejado |
| REQ-OS-003 | Consultar status e histórico | Exemplo OS Service | OS | testes das APIs de consulta | planejado |
| REQ-BILL-001 | Gerar e enviar orçamento para aprovação | Exemplo Billing Service | Billing | testes de cálculo, snapshot e `QuoteGeneratedV1` | planejado |
| REQ-BILL-002 | Registrar e verificar pagamentos | Exemplo Billing Service | Billing | testes de estados e contract tests do gateway | planejado |
| REQ-BILL-003 | Atualizar a OS após pagamento | Exemplo Billing Service | Billing → OS | teste do evento `PaymentConfirmedV1` e transição da Saga | planejado |
| REQ-BILL-004 | Integrar pagamentos com Mercado Pago | Exemplo Billing Service | Billing | contract tests, fake local e evidência em credenciais de teste | planejado |
| REQ-EXEC-001 | Gerenciar fila de execução | Exemplo Execução e Produção | Execution | testes de ordenação/estado no DynamoDB | planejado |
| REQ-EXEC-002 | Atualizar diagnóstico e reparos | Exemplo Execução e Produção | Execution | testes das transições operacionais | planejado |
| REQ-EXEC-003 | Comunicar finalização ao OS Service | Exemplo Execução e Produção | Execution → OS | `ExecutionCompletedV1` e teste integrado | planejado |

## Comunicação e transação distribuída

| ID | Requisito obrigatório | Fonte | Componente | Teste/evidência planejada | Estado |
|---|---|---|---|---|---|
| REQ-COMM-001 | Definir APIs RESTful síncronas quando necessárias | Comunicação | três serviços | OpenAPI validado e contract tests | planejado |
| REQ-COMM-002 | Usar mensageria assíncrona para eventos e integração desacoplada | Comunicação / Infraestrutura | SQS/ElasticMQ | testes publish/consume reais contra ElasticMQ | planejado |
| REQ-COMM-003 | Tratar entrega duplicada e retry com segurança | Decisão necessária à mensageria | todos | testes Inbox/Outbox, duplicata, poison message e DLQ | planejado |
| REQ-SAGA-001 | Coordenar o fluxo transacional da OS com Saga Pattern | Saga Pattern | OS process manager | BDD ponta a ponta e testes da Saga | planejado |
| REQ-SAGA-002 | Implementar rollback ou compensação em falhas | Saga Pattern | OS, Billing, Execution | BDD de falha e testes por compensação | planejado |
| REQ-SAGA-003 | Documentar e justificar orquestração ou coreografia | Saga Pattern | documentação | ADR-002, README e documento final | implementado |
| REQ-SAGA-004 | Demonstrar tratamento de falhas da Saga | Vídeo | ambiente integrado | cenário BDD reproduzível e roteiro do vídeo | planejado |

## Qualidade e entrega contínua

| ID | Requisito obrigatório | Fonte | Componente | Teste/evidência planejada | Estado |
|---|---|---|---|---|---|
| REQ-QUAL-001 | Testes unitários em todos os microsserviços | Testes e Qualidade | três serviços | suites unitárias nos três pipelines | planejado |
| REQ-QUAL-002 | Ao menos um fluxo completo em BDD | Testes e Qualidade | ambiente integrado | `pytest-bdd` atravessando três serviços e broker | planejado |
| REQ-QUAL-003 | Cobertura mínima de 80% por serviço | Testes e Qualidade | três serviços | `pytest-cov --cov-fail-under=80` por pipeline | planejado |
| REQ-QUAL-004 | Validar qualidade no CI com SonarQube ou similar | Testes e Qualidade | três pipelines | Ruff, mypy, Bandit e Xenon/Radon bloqueantes; ADR-005 | planejado |
| REQ-CICD-001 | Pipeline independente por microsserviço | CI/CD | três repositórios | um workflow versionado e executado por repositório | planejado |
| REQ-CICD-002 | Pipeline executar build | CI/CD | três pipelines | Docker build bloqueante | planejado |
| REQ-CICD-003 | Pipeline executar testes automatizados | CI/CD | três pipelines | relatório pytest por workflow | planejado |
| REQ-CICD-004 | Pipeline executar verificação de qualidade | CI/CD | três pipelines | quality script e artifacts | planejado |
| REQ-CICD-005 | Pipeline realizar deploy Kubernetes | CI/CD | três pipelines | job condicionado aos gates e evidência de rollout | planejado |
| REQ-CICD-006 | `main` exigir PR e checagens automáticas | CI/CD | GitHub | evidência de branch protection | dependência externa |

## Infraestrutura, observabilidade e entregáveis

| ID | Requisito obrigatório | Fonte | Componente | Teste/evidência planejada | Estado |
|---|---|---|---|---|---|
| REQ-INFRA-001 | Implantar os serviços em Kubernetes | Infraestrutura | EKS/Kubernetes | manifests validados e rollout dos três serviços | planejado |
| REQ-INFRA-002 | Usar mensageria para Saga | Infraestrutura | SQS | Terraform, filas/DLQs e BDD | planejado |
| REQ-OBS-001 | Reutilizar observabilidade da Fase 3 | Infraestrutura | New Relic | instrumentação por serviço, logs e consultas NRQL | planejado |
| REQ-DELIV-001 | Entregar código-fonte por serviço | Repositórios Git | três repositórios | links no PDF/README | dependência externa |
| REQ-DELIV-002 | Entregar Dockerfile e manifests Kubernetes | Repositórios Git | três serviços | arquivos versionados e validação CI | planejado |
| REQ-DELIV-003 | Entregar pipelines CI/CD | Repositórios Git | três serviços | workflows versionados | planejado |
| REQ-DELIV-004 | Entregar evidências de cobertura | Repositórios Git | três serviços | artifacts e links/prints no README | planejado |
| REQ-DELIV-005 | Documentar a arquitetura de cada serviço | Repositórios Git | três serviços | README, OpenAPI e ADRs | planejado |
| REQ-DELIV-006 | Entregar Swagger ou Postman atualizado | Repositórios Git | três serviços | OpenAPI exportado e validado; collection se necessária | planejado |
| REQ-VIDEO-001 | Vídeo público ou não listado de até 15 minutos | Vídeo | equipe | link e duração no PDF | dependência externa |
| REQ-VIDEO-002 | Demonstrar fluxo completo entre microsserviços | Vídeo | ambiente integrado | roteiro vinculado ao BDD feliz | planejado |
| REQ-VIDEO-003 | Demonstrar Saga e falha | Vídeo | ambiente integrado | roteiro vinculado ao BDD de compensação | planejado |
| REQ-VIDEO-004 | Demonstrar deploy de ao menos um serviço após testes | Vídeo | CI/CD | execução gravada do workflow | dependência externa |
| REQ-VIDEO-005 | Demonstrar monitoramento e tracing distribuído | Vídeo | New Relic | consulta por `order_id`, `saga_id` e `correlation_id` | planejado |
| REQ-PDF-001 | PDF identificar participantes | Portal | equipe | checklist final | dependência externa |
| REQ-PDF-002 | PDF conter links de repositórios e vídeo | Portal | equipe | checklist final | dependência externa |
| REQ-PDF-003 | PDF conter diagrama geral | Portal | documentação | diagrama final renderizado | planejado |
| REQ-PDF-004 | PDF descrever a estratégia Saga | Portal | documentação | ADR-002 e resumo final | implementado |
| REQ-PDF-005 | PDF justificar divisão e tecnologias | Portal | documentação | ADRs 001, 003, 004 e 005 | implementado |

## Decisões aprovadas que refinam os requisitos

| ID | Decisão | Consequência verificável |
|---|---|---|
| DEC-001 | Pagamento depois do reparo e antes da entrega | teste impede `ENTREGUE` sem `ExecutionCompletedV1` e `PaymentConfirmedV1` |
| DEC-002 | Um RDS com `os_db` e `billing_db` | usuários isolados; nenhuma permissão cruzada |
| DEC-003 | DynamoDB pertence ao Execution Service | testes de repository rodam com DynamoDB Local |
| DEC-004 | SQS na AWS e ElasticMQ local | mesmo adapter boto3, mudando apenas endpoint/configuração |
| DEC-005 | Saga orquestrada dentro do OS Service | process manager persistente, sem quarto serviço |
| DEC-006 | Catálogo no Billing; consumo físico no Execution | eventos carregam snapshots, sem consulta cruzada de banco |
| DEC-007 | Quality gates executados no runner | nenhuma dependência de SonarCloud |
| DEC-008 | Rotas separadas no API Gateway | deploys independentes sobre EKS/rede compartilhados |

## Lacunas externas controladas

Não são lacunas arquiteturais: dependem de autorização ou informação externa e permanecem rastreadas como `dependência externa`.

- criação dos repositórios remotos e configuração de branch protection;
- credenciais de teste do Mercado Pago;
- confirmação das permissões SQS/DynamoDB do AWS Academy Sandbox;
- deploy AWS e coleta de evidências reais;
- nomes/identificação dos participantes, links finais e gravação do vídeo.
