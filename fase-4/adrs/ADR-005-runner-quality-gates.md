# ADR-005 — Quality gates executados no runner

## Estado

Aceita em 2026-11-08.

## Contexto

O enunciado exige SonarQube ou ferramenta similar no CI. Foi decidido não usar SonarCloud nem depender de um serviço externo. Subir SonarQube completo em cada GitHub-hosted runner adicionaria tempo, memória, Elasticsearch e fragilidade sem persistência útil de histórico.

## Decisão

Adotar um conjunto equivalente de verificações executadas dentro do runner e bloqueantes:

- Ruff: lint e problemas comuns;
- Black: formato;
- mypy: tipagem estática;
- Bandit: segurança estática;
- Xenon/Radon: complexidade ciclomática;
- pytest + pytest-cov: comportamento e cobertura mínima de 80%;
- validações de OpenAPI, Docker, Kubernetes e Terraform conforme o serviço.

Cada repositório fornece `scripts/quality.sh` como entrada única local/CI e publica relatórios como artifacts.

## Alternativas consideradas

### SonarCloud

Rejeitado por decisão explícita de não usar análise em cloud externa.

### SonarQube efêmero no runner

Rejeitado porque consome recursos significativos, demora para inicializar e perde o principal benefício do produto: histórico centralizado.

### Apenas Black, lint e cobertura

Rejeitado por não cobrir tipagem, segurança e complexidade, ficando aquém de uma ferramenta equivalente.

## Consequências

- nenhuma conta ou token de qualidade externo;
- feedback reproduzível localmente;
- quality gate falha antes de build/publicação/deploy;
- limiares precisam ser versionados e justificados;
- não haverá dashboard histórico agregado como no SonarQube; artifacts e checks do GitHub preservam evidências por execução.

## Requisitos relacionados

REQ-QUAL-001 a REQ-QUAL-004, REQ-CICD-002 a REQ-CICD-004 e DEC-007.
