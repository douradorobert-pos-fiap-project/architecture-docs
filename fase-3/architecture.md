# Arquitetura da solução — Fase 3

## 1. Visão geral

A entrega da Fase 3 implementa uma aplicação monolítica modular para operação de uma oficina mecânica. A API FastAPI é empacotada em container, executada no Amazon EKS e persiste dados em PostgreSQL no Amazon RDS. O tráfego externo foi modelado para entrar por um API Gateway HTTP API, atravessar um VPC Link e um Network Load Balancer e alcançar os pods por meio de um `TargetGroupBinding`.

A aplicação também invoca de forma síncrona uma AWS Lambda que valida os dígitos de um CPF. Essa validação não é autenticação por CPF. A autenticação entregue é administrativa, baseada em credenciais fixas e JWT emitido pela própria API.

O [diagrama principal](architecture.mmd) e os [diagramas complementares](diagrams/) representam somente conexões sustentadas pelo código da release. Eles não comprovam que os recursos estejam atualmente provisionados.

## 2. Contexto e componentes

| Componente | Responsabilidade | Evidência principal |
|---|---|---|
| API FastAPI | Interface HTTP, autenticação administrativa e composição dos casos de uso | `tech-challenge-fiap/src/api` |
| Camada de aplicação | DTOs, portas e orquestração dos casos de uso | `tech-challenge-fiap/src/application` |
| Domínio | Entidades, value objects, regras de orçamento e ciclo de vida da OS | `tech-challenge-fiap/src/domain` |
| Infraestrutura da aplicação | SQLAlchemy, JWT, Lambda CPF, e-mail e telemetria | `tech-challenge-fiap/src/infrastructure` |
| PostgreSQL/RDS | Persistência relacional | `database-infra/terraform/main.tf` |
| Lambda CPF | Validação de formato e dígitos verificadores de CPF | `tech-challenge-fiap-lambda/src/cpf_validator` |
| API Gateway | Ponto de entrada HTTP e access logs | `shared-infra/terraform/api_gateway.tf` |
| NLB e TargetGroupBinding | Encaminhamento do Gateway aos endpoints Kubernetes | `shared-infra/terraform/networking.tf` e `tech-challenge-fiap/k8s/target-group-binding.yaml` |
| EKS | Execução da API, Job Alembic, HPA e componentes de coleta | `shared-infra/terraform/eks.tf` e `tech-challenge-fiap/k8s` |
| New Relic | APM da aplicação, métricas, eventos e logs do cluster | `shared-infra/terraform/monitoring.tf` e `tech-challenge-fiap/src/infrastructure/observability` |

## 3. Organização interna do monólito

A estrutura segue uma separação inspirada em arquitetura hexagonal/clean architecture:

1. `src/api` recebe e valida os contratos HTTP, resolve dependências e converte erros conhecidos em respostas HTTP.
2. `src/application` contém os casos de uso e depende de portas de repositório e de integrações externas.
3. `src/domain` concentra entidades e invariantes sem depender de FastAPI ou SQLAlchemy.
4. `src/infrastructure` implementa persistência, autenticação, observabilidade e adaptadores externos.

As rotas instanciam os casos de uso diretamente e recebem repositórios SQLAlchemy por `Depends`. Não há um barramento de mensagens: as operações são síncronas e executadas no processo da API.

## 4. Capacidades HTTP

| Prefixo/rota | Capacidade | Proteção no FastAPI |
|---|---|---|
| `GET /health` | Saúde e versão da aplicação | Pública |
| `/api/v1/auth` | Login e inspeção do token atual | Login público; `/me` autenticado |
| `/api/v1/clientes` | Criar, listar, consultar, atualizar e desativar clientes | JWT |
| `/api/v1/veiculos` | CRUD de veículos | JWT |
| `/api/v1/servicos` | CRUD de serviços | JWT |
| `/api/v1/pecas` | CRUD e ajuste de estoque | JWT |
| `/api/v1/ordens-servico` | Abrir, listar, detalhar e alterar status | JWT, exceto aprovação descrita abaixo |
| `POST /api/v1/ordens-servico/{id}/orcamento/aprovar` | Aprovar ou recusar orçamento | Sem `CurrentUserDep` na release |
| `GET /api/v1/public/ordens-servico/{id}/status` | Consultar status da OS | Pública |

Evidência: `tech-challenge-fiap/src/api/routes/*.py`.

## 5. Autenticação e autorização entregues

O endpoint `/api/v1/auth/login` aceita OAuth2 Password Form. O código compara o usuário com `admin` e a senha com um hash de `secret`, criado em memória durante a inicialização. Em caso de sucesso, emite JWT HS256 com `sub=admin` e `role=admin`. O segredo e a expiração são configuráveis por ambiente.

As rotas protegidas validam o Bearer token por `OAuth2PasswordBearer` e `decode_access_token`. Não existe cadastro de usuários, persistência de identidade, autenticação por CPF nem autorização granular por papel.

O Terraform de `shared-infra` cria uma Lambda authorizer JWT, porém as rotas `ANY /` e `ANY /{proxy+}` não possuem `authorization_type` nem `authorizer_id`. Portanto, a evidência da release mostra autenticação efetiva no FastAPI, não no API Gateway.

Fontes: `src/api/routes/auth_routes.py`, `src/api/dependencies.py`, `src/infrastructure/auth/jwt_handler.py`, `shared-infra/terraform/api_gateway.tf` e `shared-infra/terraform/lambda_authorizer.tf`.

## 6. Domínio e fluxo da ordem de serviço

Uma ordem associa cliente e veículo e guarda snapshots dos serviços e peças incluídos no orçamento. O cálculo soma serviços e subtotais de peças usando o value object `Dinheiro`.

Ao abrir uma OS, o caso de uso:

1. valida a existência do cliente e do veículo;
2. consulta serviços e peças indicados;
3. calcula o orçamento;
4. cria a ordem em `RECEBIDA`;
5. transita para `DIAGNOSTICO`;
6. transita para `AGUARDANDO_APROVACAO`;
7. persiste e emite `ServiceOrderCreated`.

Transições permitidas:

```text
RECEBIDA → DIAGNOSTICO → AGUARDANDO_APROVACAO → EM_EXECUCAO → FINALIZADA → ENTREGUE
     └────────────┴──────────────────┴──────────────→ CANCELADA
```

A aprovação do orçamento leva a OS para `EM_EXECUCAO`; a recusa leva a `CANCELADA`. Ordens entregues são marcadas como deletadas logicamente.

Fontes: `src/application/usecases/ordem_servico`, `src/domain/entities/ordem_servico.py`, `src/domain/services/calculo_orcamento.py` e `src/domain/value_objects/status_os.py`.

## 7. Modelo persistente

O Alembic cria sete tabelas: `clientes`, `veiculos`, `servicos`, `pecas`, `ordens_servico`, `itens_servico` e `itens_peca`.

Os itens da ordem guardam nome e preço capturados no momento do orçamento. Os identificadores de serviço e peça nesses itens não são declarados como chaves estrangeiras na migration, embora a ordem possua FKs para cliente e veículo.

Fonte: `tech-challenge-fiap/migrations/versions/001_initial_schema.py`.

## 8. Fluxo de uma requisição

1. O cliente chama o endpoint do API Gateway.
2. A rota proxy preserva o caminho e usa a integração `HTTP_PROXY`.
3. O VPC Link encaminha ao listener TCP/80 do NLB.
4. O NLB usa um target group do tipo `ip`.
5. O `TargetGroupBinding` registra os endpoints do Service `oficina-api`.
6. O Service encaminha para a porta 8000 dos pods FastAPI.
7. O middleware cria ou reutiliza `X-Correlation-ID` e registra duração/status.
8. A rota executa o caso de uso e os repositórios acessam o RDS.
9. Na criação de cliente, a API também pode invocar a Lambda CPF.
10. A resposta retorna pelo mesmo caminho e inclui `X-Correlation-ID`.

Veja [request-flow.mmd](diagrams/request-flow.mmd).

## 9. Limites e elementos não conectados

- Autenticação por CPF não existe.
- A integração `lambda_cpf` do API Gateway não possui rota associada.
- A Lambda authorizer não está associada às rotas proxy.
- O `EmailAdapter` e as portas de notificação não são injetados pelas rotas.
- O ECR `cpf-validator` não é usado pelo deploy ZIP da Lambda.
- O Terraform Kind em `tech-challenge-fiap/terraform` é uma alternativa local, não o deploy EKS.
- Consultas NRQL no README são sugestões, não dashboards provisionados.
- Não foram encontrados alertas New Relic ou monitores sintéticos versionados.
- A existência do código Terraform não comprova que a infraestrutura esteja ativa.

## 10. Referências

- [Integrações](integrations.md)
- [Infraestrutura e operação](infrastructure.md)
- [Releases analisadas](releases.md)
- [Dependências entre repositórios](diagrams/repository-dependencies.mmd)
