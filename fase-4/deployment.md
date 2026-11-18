# Implantação

Cada repositório executa pipeline independente. Em pull requests, a pipeline valida qualidade, testes/cobertura e build da imagem sem publicar ou implantar. O deploy é iniciado deliberadamente por `workflow_dispatch`; a pipeline então publica a imagem no ECR com tag do SHA, executa migrations quando aplicável e atualiza o Deployment daquele serviço. O merge em `main` não inicia deploy sozinho.

Em 17/11/2026, as execuções manuais abaixo terminaram com sucesso e publicaram artifacts `quality-reports-*` contendo `coverage.xml` e JUnit:

| Serviço | Run | Testes | Cobertura |
|---|---|---:|---:|
| OS | [44119565683](https://github.com/douradorobert-pos-fiap-project/os-service/actions/runs/44119565683) | 67 | 93,18% |
| Billing | [44157173795](https://github.com/douradorobert-pos-fiap-project/billing-service/actions/runs/44157173795) | 84 | 91,34% |
| Execution | [44119569387](https://github.com/douradorobert-pos-fiap-project/execution-service/actions/runs/44119569387) | 56 | 86,96% |

O sandbox também foi observado com cluster EKS ativo, réplicas prontas e uma compra de teste concluída. Veja [current-status.md](current-status.md) para detalhes e limites. A proteção de `main` continua pendente de configuração pelo responsável.

Terraform deve seguir `fmt`, `init`, `validate`, `plan` revisado e somente então `apply` autorizado. Após cada deploy, validar health checks e rollout. O fluxo de pagamento validado foi realizado em sandbox, sem cobrança real; automação BDD não substitui a evidência de uma compra real de teste.
