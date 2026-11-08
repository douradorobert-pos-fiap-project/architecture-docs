# ADR-001 — Limites dos microsserviços

## Estado

Aceita em 2026-11-08.

## Contexto

O monólito da Fase 3 mantém clientes, veículos, catálogo, peças, orçamento e OS em um único schema. A abertura da OS consulta cinco repositórios, calcula o orçamento e avança diretamente até `AGUARDANDO_APROVACAO`. A Fase 4 exige ao menos três microsserviços independentes sem acesso cruzado a bancos.

## Decisão

Adotar três bounded contexts:

- **OS Service:** clientes, veículos, identidade e estado global da OS, histórico e coordenação da Saga.
- **Billing Service:** catálogo comercial, preços, orçamento, aprovação, pagamento e Mercado Pago.
- **Execution Service:** diagnóstico, fila, reparos, peças e consumo operacional.

O Billing registra snapshots financeiros. O Execution registra a realidade operacional. O OS mantém apenas projeções necessárias para consulta e coordenação, atualizadas por eventos.

## Alternativas consideradas

### Reproduzir literalmente os módulos do monólito

Rejeitada porque preservaria o acoplamento entre abertura, diagnóstico e orçamento e criaria chamadas síncronas em cadeia.

### Criar serviços adicionais para cliente, veículo, catálogo, estoque e pagamento

Rejeitada porque aumentaria repositórios, bancos, pipelines e falhas distribuídas sem necessidade acadêmica ou operacional demonstrada.

### Manter catálogo e peças integralmente no Execution

Rejeitada porque preço e composição do orçamento são autoridade financeira. O Execution recebe snapshots e mantém quantidade/consumo físico.

## Consequências

- três ciclos de release e persistências independentes;
- duplicação controlada por projeções e snapshots;
- consistência eventual entre estados globais, financeiros e operacionais;
- cliente/veículo permanecem no OS Service, evitando um quarto contexto;
- mudanças em contratos de eventos exigem versionamento e compatibilidade.

## Requisitos relacionados

REQ-ARCH-001 a REQ-ARCH-003, REQ-DATA-001 a REQ-DATA-004, REQ-OS-001 a REQ-EXEC-003.
