# Integrações e dependências — Fase 3

## 1. Mapa de integrações

| Origem | Destino | Mecanismo | Contrato/configuração |
|---|---|---|---|
| Cliente externo | API Gateway | HTTPS/HTTP API | Rotas `ANY /` e `ANY /{proxy+}` |
| API Gateway | NLB | `HTTP_PROXY` por VPC Link | Listener ARN, timeout de 30 s |
| NLB | Pods EKS | TCP/80, targets do tipo `ip` | TargetGroupBinding para Service `oficina-api:80` |
| FastAPI | PostgreSQL/RDS | SQLAlchemy + psycopg2 | `DATABASE_URL` |
| FastAPI | Lambda CPF | AWS SDK `Invoke` síncrono | `{"cpf":"..."}` → `{"valid":bool}` |
| FastAPI | New Relic | Agente Python | APM, traces e eventos customizados |
| Containers/EKS | New Relic | Helm `nri-bundle` | métricas, eventos e logs |
| API Gateway | CloudWatch Logs | Access log nativo | JSON com status e latência |
| Pipeline da aplicação | States Terraform | Backend S3 | outputs de rede, EKS, RDS, ECR, Lambda e JWT |

## 2. Entrada HTTP: API Gateway, NLB e EKS

O API Gateway HTTP API possui estágio `$default` com implantação automática e duas rotas proxy. Ambas apontam para uma integração `HTTP_PROXY` cujo URI é o listener do NLB. A conexão ocorre por VPC Link nas sub-redes privadas.

O NLB é público, escuta TCP/80 e encaminha para um target group do tipo `ip`. O manifesto `TargetGroupBinding` associa esse target group ao Service Kubernetes `oficina-api`, porta 80. O Service é `ClusterIP` e encaminha ao `targetPort` nomeado `http`, porta 8000 do container.

Fontes:

- `shared-infra/terraform/api_gateway.tf`;
- `shared-infra/terraform/networking.tf`;
- `tech-challenge-fiap/k8s/service.yaml`;
- `tech-challenge-fiap/k8s/target-group-binding.yaml`;
- `tech-challenge-fiap/k8s/deployment.yaml`.

### Saúde

O endpoint `GET /health` é usado por:

- startup, readiness e liveness probes do Deployment;
- health check HTTP do target group do NLB;
- validação direta por operadores.

Ele confirma apenas que o processo HTTP responde; não testa banco, Lambda ou New Relic.

## 3. Aplicação e PostgreSQL

O `DATABASE_URL` é montado pela pipeline com os outputs do state de `database-infra` e o secret `DB_PASSWORD` do GitHub Actions. O valor é armazenado no Secret Kubernetes `oficina-secrets` e lido pelo `pydantic-settings`.

A aplicação cria um engine SQLAlchemy e sessões síncronas. Em cada dependência de rota, uma implementação concreta de repositório recebe a sessão e traduz modelos SQLAlchemy para entidades de domínio.

Antes do rollout, um Job executa `alembic upgrade head`. O Job tenta conectar ao banco até 30 vezes, com intervalo de dois segundos, e o workflow aguarda até 360 segundos pelo resultado.

Fontes: `src/infrastructure/database/session.py`, `src/infrastructure/database/repositories`, `k8s/migration-job.yaml`, `.github/workflows/pipeline.yml` e `terraform/infra/main.tf`.

### Contrato persistente relevante

- IDs são UUIDs serializados em colunas `String(36)`.
- Valores monetários usam `Numeric(10,2)` no banco.
- Cliente possui CPF/CNPJ único.
- Veículo possui placa única e FK para cliente.
- Ordem possui FKs para cliente e veículo.
- Itens de orçamento têm FK para a ordem, mas não FK declarada para os catálogos de serviço e peça.
- Desativação de cliente, serviço e peça é lógica; entrega/ocultação da OS também usa estado lógico.

## 4. Aplicação e Lambda de CPF

### Chamada

O `CreateClienteUseCase` cria primeiro o value object `CpfCnpj` e, depois, usa `CpfValidatorAdapter`. Quando `CPF_VALIDATOR_LAMBDA_ARN` está configurado, o adaptador chama:

```text
Lambda.Invoke
InvocationType: RequestResponse
FunctionName: <ARN configurado>
Payload: {"cpf":"12345678909"}
```

Resposta esperada:

```json
{"valid": true}
```

A Lambda normaliza caracteres não numéricos, exige 11 dígitos, rejeita sequências repetidas e calcula os dois dígitos verificadores.

### Falhas e fallback

Se o ARN estiver vazio, ocorrer `ClientError` ou qualquer exceção inesperada, o adaptador volta à validação local por `CpfCnpj`. Erros de invocação geram evento `IntegrationError` no New Relic. Como há fallback, indisponibilidade da Lambda não implica necessariamente falha da criação do cliente.

### Permissões

O ServiceAccount `oficina-api` não contém annotation IRSA na release. O fluxo pressupõe que o SDK no pod obtenha credenciais por outro mecanismo disponível no cluster; a pipeline e o comentário do Load Balancer Controller indicam uso da role dos nodes via IMDS. A permissão efetiva de `lambda:InvokeFunction` depende da `LabRole` externa e não pode ser comprovada apenas pelos quatro repositórios.

Fontes:

- `tech-challenge-fiap/src/application/usecases/cliente/crud_usecases.py`;
- `tech-challenge-fiap/src/infrastructure/adapters/cpf_validator_adapter.py`;
- `tech-challenge-fiap-lambda/src/cpf_validator/handler.py`;
- `tech-challenge-fiap-lambda/src/cpf_validator/validator.py`;
- `tech-challenge-fiap/k8s/service-account.yaml`.

## 5. Autenticação e JWT

O login administrativo emite um JWT assinado com `JWT_SECRET`. A pipeline lê esse valor do Secrets Manager por meio do state compartilhado e o injeta no Secret Kubernetes.

Há dois validadores JWT no código entregue:

1. o FastAPI valida tokens nas rotas que usam `CurrentUserDep`;
2. uma Lambda authorizer foi declarada em `shared-infra`.

Somente o primeiro está conectado ao fluxo das rotas. A authorizer não foi associada às rotas do API Gateway. Além disso, a variável `jwt_secret_arn` usada pela authorizer não referencia automaticamente o secret criado no mesmo Terraform e está vazia no `terraform.tfvars` da release.

## 6. Observabilidade

O middleware HTTP aceita `X-Correlation-ID`, limitado a 128 caracteres, ou gera um UUID. O identificador entra nos logs JSON e nos eventos customizados e é devolvido na resposta. Não há cliente HTTP próprio para propagá-lo à Lambda; o SDK e o agente podem manter seus próprios contextos, mas o payload CPF não inclui o correlation ID.

Eventos customizados:

| Evento | Momento | Atributos relevantes |
|---|---|---|
| `ServiceOrderCreated` | Criação de OS | `order_id`, `status`, `correlation_id` |
| `ServiceOrderStatusChanged` | Aprovação/recusa ou mudança de estado | estados anterior/novo |
| `ServiceOrderStatusDuration` | Saída de um estado | estado e `duration_ms` |
| `IntegrationError` | Erro em integração instrumentada | integração, operação e tipo de erro |

## 7. Dependências entre os repositórios

Consulte [repository-dependencies.mmd](diagrams/repository-dependencies.mmd).

### Ordem lógica de provisionamento

1. `tech-challenge-fiap-lambda`: cria a função consultada por nome.
2. `shared-infra`: cria VPC, EKS, entrada HTTP, ECR, secrets e New Relic; lê a Lambda existente.
3. `database-infra`: lê o state compartilhado e instala o RDS na VPC.
4. `tech-challenge-fiap`: lê os dois states, publica a imagem e implanta a aplicação.

Essa ordem não elimina os pré-requisitos externos: bucket S3 de state, `LabRole`, credenciais AWS, secrets de CI e licença New Relic precisam existir.

## 8. Integrações declaradas, mas não efetivas

| Elemento | Evidência | Situação na release |
|---|---|---|
| API Gateway → Lambda CPF | recurso `aws_apigatewayv2_integration.lambda_cpf` | Sem rota associada |
| API Gateway → Lambda authorizer | authorizer e permissão de invoke | Sem associação às rotas |
| Aplicação → e-mail | porta e `EmailAdapter` | Não injetado pelos endpoints |
| ECR `cpf-validator` → Lambda | repositório ECR compartilhado | Lambda usa ZIP, não imagem |
| Dashboards/alertas New Relic | NRQL sugerido em README | Sem recurso versionado de dashboard ou alerta |
