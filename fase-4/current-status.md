# Estado atual da Fase 4

Atualizado em **17/11/2026** com evidências do GitHub Actions, API Gateway, EKS e do fluxo de pagamento no sandbox. Este registro distingue o que foi observado do que ainda precisa de evidência de entrega.

## Validação no sandbox

- O cluster `oficina-sandbox` estava `ACTIVE`.
- Os três Deployments de API estavam `2/2` disponíveis; os três workers estavam `1/1` prontos.
- Uma ordem sandbox de **R$ 1,00** percorreu OS, Execution, Billing e Mercado Pago. O Billing registrou `APPROVED`, o webhook `order` recebeu HTTP `200` e a ordem terminou `DELIVERED`.
- Uma tentativa de simulação manual no painel do Mercado Pago respondeu HTTP `401` por assinatura inválida. Ela foi distinta do webhook da compra real de teste, que foi aceito; portanto, o erro da simulação não representa falha geral do endpoint nem impediu o fluxo pago.
- A API Gateway possui a rota `POST /api/v1/webhooks/mercado-pago`, sem autenticação na camada Gateway, integrada ao listener do ALB interno. A assinatura é validada pelo Billing.
- Algumas notificações antigas `topic_merchant_order_wh` responderam `422`; são diferentes do evento `order` usado pela integração atual.

Essas observações comprovam uma execução ponta a ponta no ambiente de teste, mas não substituem testes automatizados de todas as transições nem demonstram ingestão de telemetria no painel New Relic.

## Pipelines e cobertura

As últimas execuções `workflow_dispatch` de 17/11/2026 terminaram com sucesso. Cada workflow publica o relatório `coverage.xml` e o relatório JUnit como artifact `quality-reports-<repositório>`.

| Serviço | Resultado | Testes | Cobertura | Execução |
|---|---:|---:|---:|---|
| OS | Sucesso | 67 | 93,18% | [Pipeline OS](https://github.com/douradorobert-pos-fiap-project/os-service/actions/runs/44119565683) |
| Billing | Sucesso | 84 | 91,34% | [Pipeline Billing](https://github.com/douradorobert-pos-fiap-project/billing-service/actions/runs/44157173795) |
| Execution | Sucesso | 56 | 86,96% | [Pipeline Execution](https://github.com/douradorobert-pos-fiap-project/execution-service/actions/runs/44119569387) |

Os três valores superam o piso de 80% configurado nos quality gates.

## Saga e compensação

O OS Service mantém o estado da Saga e coordena os participantes por eventos. As compensações automáticas existentes cobrem a recusa do orçamento e falhas/cancelamentos antes do início do reparo. Falhas depois que o reparo começou, pagamento rejeitado e reembolso encaminham o caso para intervenção manual. Como reparo executado e pagamento confirmado não podem ser desfeitos por rollback técnico, essa intervenção é um limite deliberado, mas não equivale a compensação automática em toda etapa do requisito acadêmico.

O cenário BDD está versionado em `bdd/`. Ele cobre o fluxo feliz, falha antes do reparo e confirmação duplicada, usando `TestClient`, SQLite, Moto e um fake de pagamento. O harness aplica algumas transições da Saga diretamente; não executa os três serviços em containers e não exercita a entrega real pelo SQS. Essa distinção deve ser mantida na apresentação.

## Entrega ainda pendente

- Regras de proteção de `main` são geridas no nível da organização, conforme informado pelo responsável do projeto.
- Ambiente integrado local com Docker/Kind; o runbook anterior foi removido porque essa configuração ainda não foi aplicada e validada.
- Evidência de ingestão e tracing distribuído no New Relic. [Dashboards JSON foram preparados](new-relic/dashboards/README.md) com os eventos atuais, mas a ingestão e os gráficos ainda precisam ser confirmados na conta.
- Vídeo de até 15 minutos, que será gravado pela equipe.
- PDF final com participantes, links, diagrama e evidências.

O deploy permanece **manual por decisão**: `workflow_dispatch` inicia a pipeline; build, migrations e rollout são automatizados dentro dela. O merge em `main` não dispara deploy automaticamente.
