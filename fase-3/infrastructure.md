# Infraestrutura, entrega e observabilidade — Fase 3

## 1. Distribuição de responsabilidades

| Repositório | Recursos/artefatos |
|---|---|
| `shared-infra` | Rede, EKS, NLB, API Gateway, ECR, Secrets Manager, Lambda authorizer, CloudWatch e New Relic |
| `database-infra` | RDS PostgreSQL, subnet group e security group |
| `tech-challenge-fiap` | Imagem da API, manifests Kubernetes, migrações e ponte de remote states |
| `tech-challenge-fiap-lambda` | Código e Terraform da Lambda CPF |

## 2. Terraform e estado

### Backends

| Escopo | Bucket | Chave |
|---|---|---|
| Compartilhado | `terraform-state-264040538379-us-east-1` | `sandbox/terraform.tfstate` |
| Banco | `terraform-state-264040538379-us-east-1` | `database/terraform.tfstate` |
| Ponte da aplicação | `terraform-state-264040538379-us-east-1` | `app/terraform.tfstate` |

Os três backends usam locking nativo do S3 (`use_lockfile = true`). O bucket não é criado pelos códigos analisados e é pré-requisito.

O Terraform da Lambda não declara backend remoto; sem configuração externa, usa state local.

### Ponte da aplicação

`tech-challenge-fiap/terraform/infra` não provisiona o EKS nem o RDS. Ele lê os states compartilhado e de banco, lê a versão do segredo JWT e publica outputs consumidos pelo workflow da aplicação.

## 3. Rede AWS

`shared-infra` define, no ambiente sandbox:

- VPC `10.0.0.0/16`;
- sub-redes públicas `10.0.1.0/24` e `10.0.2.0/24`;
- sub-redes privadas `10.0.10.0/24` e `10.0.11.0/24`;
- zonas `us-east-1a` e `us-east-1b`;
- Internet Gateway;
- um NAT Gateway e um Elastic IP por zona;
- tabela pública com rota para o Internet Gateway;
- uma tabela privada por zona com rota pelo NAT correspondente.

O NLB é internet-facing nas sub-redes públicas. O VPC Link fica nas privadas. Os nodes EKS e o RDS também ficam nas privadas.

Fonte: `shared-infra/terraform/vpc.tf` e `environments/sandbox/terraform.tfvars`.

## 4. Amazon EKS

Configuração declarada:

- Kubernetes 1.31;
- control plane associado às sub-redes públicas e privadas;
- endpoint público e privado;
- endpoint público permitido para `0.0.0.0/0`;
- node group `ON_DEMAND` em sub-redes privadas;
- `t3.medium`;
- desejado 2, mínimo 1, máximo 4 nodes;
- IMDSv2 obrigatório no launch template;
- add-ons VPC CNI, CoreDNS e kube-proxy;
- AWS Load Balancer Controller 1.7.1 via Helm.

A mesma `LabRole` externa é usada pelo control plane, node group e Lambda authorizer. O conteúdo e as permissões dessa role não estão versionados.

Fonte: `shared-infra/terraform/eks.tf` e `variables.tf`.

## 5. Entrada da aplicação

### NLB

- público e cross-zone;
- listener TCP/80;
- target group TCP/80 do tipo `ip`;
- health check HTTP em `/health`;
- ingress 8000 no security group do cluster a partir das CIDRs públicas.

### API Gateway

- HTTP API;
- CORS com origem `*` no sandbox;
- métodos GET, POST, PUT, PATCH, DELETE e OPTIONS;
- VPC Link em sub-redes privadas;
- proxy para o listener do NLB;
- estágio `$default` com auto deploy;
- access logs por 30 dias no CloudWatch.

O security group do VPC Link permite entrada TCP/80 de qualquer origem e toda saída. Como security groups de VPC Link normalmente são relevantes no tráfego de saída, essa regra de entrada é mais ampla que a necessidade demonstrada.

Fontes: `shared-infra/terraform/networking.tf` e `api_gateway.tf`.

## 6. RDS PostgreSQL

| Propriedade | Valor na release |
|---|---|
| Engine | PostgreSQL 16 |
| Classe | `db.t4g.micro` |
| Armazenamento | 20 GiB gp3 |
| Porta | 5432 |
| Banco inicial | `oficina` |
| Público | Não |
| Multi-AZ | Não |
| Backup | 1 dia |
| Proteção contra exclusão | Não |
| Snapshot final | Desabilitado por padrão |

O subnet group exige ao menos duas sub-redes privadas. O security group aceita PostgreSQL de toda a CIDR da VPC compartilhada, não somente do security group dos workloads EKS.

Fonte: `database-infra/terraform/main.tf`, `data.tf`, `variables.tf` e `terraform/environments/sandbox/terraform.tfvars`.

## 7. ECR e Lambda

O repositório compartilhado cria:

- `application`, usado pela pipeline da API;
- `cpf-validator`, sem consumidor no deploy da release.

Ambos têm tags imutáveis, scan no push, criptografia AES-256 e política para manter as 20 imagens mais recentes.

A Lambda CPF é criada separadamente com runtime Python 3.12, handler `cpf_validator.handler.handler` e pacote ZIP gerado pelo provider Archive. Ela usa a `LabRole` informada por variável.

## 8. Kubernetes

### Objetos aplicados no EKS

- Namespace `oficina`;
- ConfigMap `oficina-config`;
- ServiceAccount `oficina-api`;
- Service `oficina-api` do tipo `ClusterIP`;
- Deployment `oficina-api`;
- Job `alembic-migrations`;
- TargetGroupBinding;
- HPA.

Existe também manifesto completo do Metrics Server, porém o workflow AWS da aplicação não o aplica. O HPA pressupõe que uma API de métricas já esteja disponível no cluster. O Terraform local baseado em Kind aplica o Metrics Server, mas é um caminho distinto.

### Deployment

- duas réplicas iniciais;
- container na porta 8000;
- requests de `100m` CPU e `128Mi` RAM;
- limits de `500m` CPU e `512Mi` RAM;
- probes em `/health`;
- `imagePullSecret` criado dinamicamente para o ECR;
- configurações por ConfigMap e Secret.

### HPA

- mínimo 2 e máximo 10 pods;
- CPU alvo de 70%;
- memória alvo de 80%;
- estabilização de 30 s para subida e 300 s para descida.

O máximo de pods é independente do máximo de quatro nodes; não há Cluster Autoscaler versionado.

### Secret

No deploy AWS, o workflow gera `oficina-secrets` com:

- `JWT_SECRET`;
- `DATABASE_URL`;
- `CPF_VALIDATOR_LAMBDA_ARN`;
- `NEW_RELIC_LICENSE_KEY`;
- `SMTP_USER`;
- `SMTP_PASSWORD`.

O arquivo `k8s/secret.yaml` é apenas um modelo versionado e não representa os valores do ambiente.

## 9. CI/CD

### Aplicação

#### Pull request para `main`

1. checkout;
2. Python 3.12 e Poetry;
3. instalação de dependências;
4. Black e isort;
5. pytest com cobertura mínima de 80%;
6. build Docker sem publicação.

#### Push para `main`

Após a validação:

1. login no ECR;
2. build e push de `application:<github.sha>`;
3. `terraform apply -refresh-only` no state-ponte;
4. leitura dos outputs de RDS, EKS, ECR, Lambda e JWT;
5. configuração do kubeconfig;
6. descoberta do target group e security group por AWS CLI;
7. substituição da imagem e placeholders nos manifests no runner;
8. criação/atualização dos Secrets Kubernetes;
9. validação do AWS Load Balancer Controller;
10. aplicação dos manifests;
11. recriação e espera do Job Alembic;
12. aplicação do TargetGroupBinding e HPA;
13. espera do rollout.

O `workflow_dispatch` está declarado, mas o job `deploy` depende de `build-and-push`, que é pulado fora de push para `main`. Sem `always()` ou fluxo alternativo, o despacho manual pode não executar o deploy.

### Shared infra

Pull requests executam fmt, init, validate e plan. Push em `main` faz um bootstrap direcionado de EKS/node group, configura kubeconfig, sincroniza credenciais do Load Balancer Controller e aplica o plano completo.

### Banco

Pull requests executam validação e plan. Push em `main` também executa apply por scripts do repositório.

### Lambda

Push em `main` executa testes, cobertura, Black, isort, Terraform fmt/validate/plan e apply. Não há gatilho de pull request no workflow da release.

## 10. Observabilidade

### New Relic no cluster

`shared-infra` instala o chart oficial `nri-bundle` 8.0.10 no namespace `newrelic`, com:

- kube-state-metrics;
- eventos Kubernetes;
- coleta de logs de containers;
- nome do cluster EKS;
- license key sensível fornecida pelo CI.

### New Relic na aplicação

A dependência `newrelic` está fixada no lock em 10.17.0. A inicialização ocorre somente se houver license key. O código produz logs JSON em stdout, correlation ID e eventos de negócio/integração.

### CloudWatch

O API Gateway grava access logs JSON em log group próprio, com retenção de 30 dias. Não há encaminhamento CloudWatch → New Relic no código analisado.

### Ausências comprovadas

Não foram encontrados recursos versionados para:

- dashboard New Relic;
- política/condição de alerta;
- monitor sintético;
- alerta de disponibilidade;
- exportação do CloudWatch para New Relic.

As consultas NRQL documentadas no README da aplicação são instruções operacionais, não objetos provisionados.

## 11. Reprodução da solução

Ordem recomendada a partir dos códigos entregues:

1. preparar conta AWS, bucket S3 de state e `LabRole` com permissões compatíveis;
2. configurar secrets/variables exigidos pelos workflows;
3. aplicar `tech-challenge-fiap-lambda`;
4. aplicar `shared-infra`, informando a Lambda existente e a licença New Relic;
5. reconciliar `jwt_secret_arn` da authorizer caso ela deva ser usada;
6. aplicar `database-infra` com senha do banco;
7. executar a pipeline de `tech-challenge-fiap` para imagem, migração e deploy;
8. validar `/health`, migrações, targets do NLB e acesso ao banco;
9. validar separadamente ingestão no New Relic.

Essa sequência é uma reconstrução das dependências do código. Não é evidência de que os workflows executarão sem ajustes em uma conta diferente, pois existem ARNs, nomes e bucket vinculados ao ambiente acadêmico.

## 12. Riscos para a migração a microsserviços

- Um único schema concentra todos os agregados; a separação exigirá definir propriedade de dados.
- A abertura de OS consulta cinco repositórios no mesmo processo e transação implícita.
- Itens de orçamento já funcionam como snapshots, o que ajuda a desacoplar catálogos.
- Autenticação é local e rudimentar; deve ser tratada como capacidade transversal antes da divisão.
- Eventos New Relic são telemetria, não eventos de domínio transportados por mensageria.
- Não há idempotência, outbox ou broker versionado.
- A Lambda CPF possui fallback local, criando duas implementações da mesma regra.
- Configuração e deploy dependem fortemente de remote states e nomes fixos do ambiente sandbox.
