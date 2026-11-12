# Limitações conhecidas

- A sessão AWS atual não passou em `get-caller-identity`; SQS, DynamoDB, ECR e EKS não foram confirmados.
- Não houve `terraform plan` remoto, `apply`, push, configuração de branch protection ou deploy.
- Docker/cluster local não estavam disponíveis para smoke de imagem/rollout; build e deploy permanecem gates do CI.
- Credenciais sandbox do Mercado Pago não foram fornecidas; integração foi validada com fake e contract tests, sem cobrança real.
- Links remotos, participantes, vídeo e evidências visuais dependem da equipe.
- O bootstrap de bancos lógicos exige runner com acesso de rede ao RDS e permanece desabilitado por padrão.
