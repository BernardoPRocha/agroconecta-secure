# AgroConecta - Secure DevOps + ACV integrado

Bernardo Rocha - RM99209 | Eric Rodrigues - RM550249 | Renato Izumi - RM99242.
Global Solution 2026.2, ODS 2 e 13.

## O que esta versão entrega

Portal FastAPI com ACV real em `/visao/`: modelo YOLOv8n treinado para três classes de folhas de tomate, upload e câmera. RAG, sensores e cotações continuam explicitamente pendentes; não são simulados.

- Docker non-root (UID 10001), sistema de arquivos somente leitura e processo limitado.
- HTTPS automático via Caddy. Porta 8000 não publicada; métricas apenas na rede Docker.
- Terraform Azure com VM, DNS, rede, SSH restrito ao administrador e identidade OIDC para GitHub.
- CI com testes, Semgrep, Gitleaks, Trivy, smoke test do contêiner e deploy da mesma imagem por digest.
- Deploy via Azure Run Command: não depende de SSH do runner e não usa chave SSH privada no GitHub.
- Prometheus, Grafana, volumes persistentes e alerta provisionado `agroconecta-down`.

**Estado:** código corrigido e testes locais executados. Não há comprovação de deploy Azure, certificado emitido, pipeline verde ou alerta Firing nesta versão. Confira `reports/VALIDACAO.md`. Não apresente configuração como evidência de execução.

## 1. Executar no seu computador

Python 3.12, Git; Docker Desktop para os testes de contêiner. PowerShell, dentro desta pasta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q tests
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra http://localhost:8000 e clique em **Triagem de folhas de tomate**. `localhost` permite câmera; o endereço público precisa de HTTPS. Fotos não são persistidas pela aplicação. Resultados são hipóteses visuais, não diagnóstico agronômico. Ausência de detecção é inconclusiva.

Teste Docker após parar o Uvicorn:

```powershell
docker build -t agroconecta-mvp:local .
docker run -d --name agroconecta-local --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m,mode=1777 --cap-drop ALL --security-opt no-new-privileges -p 127.0.0.1:8000:8000 agroconecta-mvp:local
docker exec agroconecta-local id -u
# Esperado: 10001
Invoke-RestMethod http://localhost:8000/ready
docker stop agroconecta-local
docker rm agroconecta-local
```

## 2. Preparar Azure e repositório Secure

Publique **todo este diretório** em um repositório GitHub público de Secure, incluindo pastas ocultas `.github`, `.dockerignore`, `.gitignore` e `terraform/.terraform.lock.hcl`. O repositório ACV já existente continua sendo a fonte original do modelo; não sobrescreva seu conteúdo com este pacote.

Crie também um repositório **público** `agroconecta-mvp` no Docker Hub. A VM baixa a imagem sem senha. Em repositório privado, seria necessário configurar uma credencial de leitura na VM, o que não faz parte deste fluxo.

A Azure gera custos. A VM padrão agora é **Standard_B2ms (8 GB)** para comportar inferência CPU + observabilidade; a antiga B1s era inadequada para essa integração. Verifique preço, crédito e cota antes do `apply`. Não execute `apply` sem revisar o `plan`.

A conta usada no Terraform precisa criar recursos e atribuir papéis. Use Azure CLI e Terraform >= 1.5. No PowerShell:

```powershell
az login
az account show --query id -o tsv
# Defina a assinatura autorizada caso haja mais de uma: az account set --subscription ID
# Gere uma chave RSA de 4096 bits apenas se ainda não tiver uma; não sobrescreva sua chave.
ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\id_rsa"
$env:TF_VAR_subscription_id = (az account show --query id -o tsv).Trim()
$env:TF_VAR_github_repository = 'SEU_USUARIO/SEU_REPOSITORIO_SECURE'
$meuIp = (Invoke-RestMethod 'https://api.ipify.org').Trim()
$env:TF_VAR_ssh_allowed_cidr = "$meuIp/32"
cd terraform
terraform init
terraform fmt -check
terraform validate
terraform plan -out=deploy.tfplan
terraform apply deploy.tfplan
terraform output
cd ..
```

Se o DNS padrão já estiver ocupado, antes do plan defina `TF_VAR_dns_label` com um nome exclusivo. Guarde o estado local do Terraform com segurança: não o publique e não o perca. Reaproveite o mesmo estado para atualizações e remoção. Não é preciso alterar o Prometheus quando o DNS mudar: a coleta usa `app:8000` na rede privada Docker.

A identidade OIDC criada só confia no repositório informado e no environment **production**. Ela recebe **Virtual Machine Contributor somente no escopo desta VM**; Run Command executa como administrador da VM. Proteja quem pode alterar o workflow ou publicar na main.

## 3. Configurar GitHub Actions

No repositório Secure, crie **Settings > Environments > production**. Restrinja deployment branches a **main**. Configure revisão de deploy quando disponível. Proteja a branch main contra mudanças não revisadas.

Em production, configure estas **Variables**, com os valores correspondentes de `terraform output`:

| Variable | Output Terraform |
|---|---|
| AZURE_CLIENT_ID | github_azure_client_id |
| AZURE_TENANT_ID | github_azure_tenant_id |
| AZURE_SUBSCRIPTION_ID | github_azure_subscription_id |
| AZURE_RESOURCE_GROUP | github_azure_resource_group |
| AZURE_VM_NAME | github_azure_vm_name |
| SITE_DOMAIN | github_site_domain |

Configure os **Secrets** `DOCKERHUB_USERNAME` e `DOCKERHUB_TOKEN` no mesmo environment. O token deve poder publicar somente no repositório necessário. **Não cadastre AZURE_SSH_PRIVATE_KEY.** Não é necessário client secret Azure.

Na aba Actions, execute **AgroConecta - DevSecOps integrado** na main. Os scans e testes bloqueiam o deploy em caso de falha; achados HIGH/CRITICAL devem ser corrigidos, não ocultados. A primeira execução pode falhar por vulnerabilidades recém-publicadas, cota, configuração externa ou propagação de RBAC: leia o log, corrija e execute novamente.

O job `validate` salva a imagem já analisada. O job `deploy` carrega essa mesma imagem, publica, resolve seu digest e usa Azure Run Command. O sucesso exige `/ready` com modelo carregado e resposta HTTPS válida. O payload e a VM não recebem credenciais do Docker Hub.

A emissão do certificado exige DNS correto e portas 80/443 acessíveis. A inicialização pode levar minutos. Não use `curl -k` para ocultar falhas de TLS.

## 4. Monitoramento e teste real do alerta

Toda a stack fica na VM; Prometheus e Grafana são acessíveis apenas por túnel SSH de administração. Use o IP de `terraform output ip_publico_vm`:

```powershell
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 azureuser@SEU_IP
```

Mantenha essa conexão aberta. A senha inicial do Grafana é gerada aleatoriamente na VM no primeiro deploy. Veja-a **somente no seu terminal privado**, sem gravar prints nem logs públicos:

```bash
sudo cat /opt/agroconecta/.grafana-password
```

Abra http://localhost:3000 (usuário admin) e http://localhost:9090/targets. Há dashboard e regra `AgroConecta indisponível` já provisionados. Não é necessário criar a regra manualmente. Volumes preservam dados, alertas e certificados entre recriações de contêineres. Não use `docker compose down -v`.

A regra usa `up < 1`, avalia a cada 20 segundos e aguarda 30 segundos. No Grafana, capture estado Normal antes do teste. Em uma sessão SSH na VM:

```bash
cd /opt/agroconecta
sudo docker compose stop app
# Aguarde aproximadamente 45-90 segundos; confirme Firing no Grafana e capture o print.
sudo docker compose start app
# Confirme app saudável, target UP e recuperação para Normal.
sudo docker compose ps
sudo docker compose exec -T app id -u
```

Esse teste causa indisponibilidade temporária; execute fora da apresentação. A regra comprova **Firing no Grafana**, não envio de e-mail/WhatsApp. Um canal externo de notificação só deve ser configurado se solicitado.

Se o SSH falhar após mudar de rede, atualize `TF_VAR_ssh_allowed_cidr` e aplique o Terraform. Isso não afeta o deploy OIDC.

## 5. Coletar evidências e fechar o relatório

```powershell
python scripts/collect_evidence.py --url https://SEU_DNS_REAL --output reports/evidencias-publicas.json
```

O coletor consulta readiness, portal, ACV, proteção de métricas e faz uma inferência real. Saídas com erro impedem considerá-lo aprovado. Não inventa logs nem prints.

Anexe ao relatório: Terraform apply/VM, run aprovado no GitHub, URL HTTPS e câmera, UID 10001, target UP, dashboard, Firing e recuperação. O PDF incluído registra somente verificações locais reais e pendências externas, sem espaços preenchidos com provas fictícias.

Limites: MVP acadêmico público sem cadastro de usuários; inferência limitada em concorrência, mas sem proteção completa contra abuso/DoS. RAG, sensores e cotações ainda precisam de integração pela equipe. Segurança de produção exigiria avaliação adicional.

## Fonte do ACV

Código e modelo: https://github.com/BernardoPRocha/agroconecta-acv, commit `bf47e285c36955e41b6f676bfc2d5a2c3f311744`. Pesos preservados, sem retreinamento. PlantDoc: créditos em `examples/SOURCES.json` e `docs/PLANTDOC_LICENSE.txt`; Ultralytics segue AGPL-3.0 ou licença comercial. A documentação de ACV contém as métricas e limitações originais.

Depois da avaliação, remova recursos Azure que não serão usados, utilizando o mesmo estado Terraform. Não execute destroy enquanto a URL precisar ficar disponível para o professor.
