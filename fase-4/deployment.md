# Implantação

Cada repositório executa pipeline independente: instala dependências, roda testes/cobertura e gates locais, publica relatórios, constrói imagem, publica no ECR com tag do SHA e atualiza apenas seu Deployment. Pull requests constroem a imagem sem publicar ou implantar.

Pré-requisitos externos: repositórios remotos, proteção de `main`, secrets temporários AWS, variáveis `EKS_CLUSTER_NAME`/`K8S_DEPLOYMENT`, ECR/EKS disponíveis e credenciais de teste do Mercado Pago. Para banco, executar migrations antes do rollout.

Terraform deve seguir `fmt`, `init`, `validate`, `plan` revisado e somente então `apply` autorizado. Nenhum apply foi realizado nesta implementação. Depois do deploy, validar `/health`, rollout, logs correlacionados e um fluxo BDD/smoke sem cobrança real.
