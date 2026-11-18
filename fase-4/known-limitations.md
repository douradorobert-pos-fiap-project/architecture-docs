# Limitações conhecidas

- A execução integrada local com Docker/Kind ainda não está implementada; não há runbook ou Compose para iniciar os três serviços juntos.
- O BDD usa `TestClient`, SQLite, Moto e fake Mercado Pago; algumas transições da Saga são aplicadas diretamente e o teste não cobre transporte real de eventos.
- As compensações automáticas não cobrem falhas após o início do reparo nem pagamento recusado/reembolsado; esses caminhos exigem intervenção manual.
- A ingestão de eventos e tracing no New Relic ainda precisa ser confirmada no painel; configuração no deployment não comprova recebimento.
- O estado do AWS Academy Sandbox é temporário; EKS e workloads foram observados ativos em 17/11/2026, sem garantia de disponibilidade posterior.
- O deploy começa manualmente por `workflow_dispatch`; o merge não dispara rollout automaticamente.
- Vídeo, PDF final com participantes, links e evidências visuais ainda dependem da equipe.
- Regras de proteção de `main` são administradas no nível da organização, conforme confirmação do responsável.
