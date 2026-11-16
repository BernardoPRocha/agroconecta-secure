# Verificação da revisão Secure + ACV

Revisão de código iniciada em 15/11/2026 e empacotada em 16/11/2026.

## Executado com sucesso
- 11 testes pytest em Python 3.12: navegação, readiness com modelo real, inferência em imagem de exemplo, uploads inválidos/excessivos, falha sem modelo, métricas e configuração/payload do deploy. Log: tests-local.txt.
- Docker Compose: config --quiet aprovado; Caddy 2.10.2: validate aprovado. Isso não comprova execução dos contêineres nem emissão de certificado.
- bash -n scripts/deploy_vm.sh e node --check vision/static/app.js.
- Terraform fmt; terraform init baixou AzureRM 4.81.0 e gerou .terraform.lock.hcl.

## Limitação de validação Terraform
terraform validate não concluiu neste ambiente. O provedor falhou ao abrir seu socket Unix: "socket: operation not permitted". Isso é uma limitação do ambiente de revisão; não constitui aprovação do Terraform. O workflow exige fmt/init/validate em um runner padrão antes do deploy. Plan/apply, cotas e RBAC precisam ser verificados na conta Azure.

## Não executado aqui
- Build e execução de contêiner: não há Docker daemon disponível.
- Execução remota de Gitleaks, Semgrep e Trivy: o workflow deve passar por esses gates.
- Azure plan/apply, OIDC, Run Command, emissão de certificado e teste de URL pública.
- Renderização do dashboard no Grafana, coleta contínua, alerta Firing e recuperação.

Nenhuma captura de tela externa ou resultado de scanner foi fabricado. Arquivos em reports são evidências apenas das verificações identificadas explicitamente.
