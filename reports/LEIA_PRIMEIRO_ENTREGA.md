# AgroConecta Secure — pacote de evidências finais

**Global Solution 2026.2 — Secure DevOps Tools & Cloud Computing**

## Entregas deste pacote

- `RELATORIO_FINAL_AGROCONECTA_SECURE.pdf` — relatório com arquitetura, links e 11 capturas reais.
- `evidencias/` — capturas PNG originais selecionadas, com nomes descritivos.
- `MANIFESTO_EVIDENCIAS.txt` — relação das capturas, justificativa e SHA-256.

**Links reais:**

- Repositório: https://github.com/BernardoPRocha/agroconecta-secure
- GitHub Actions com deploy: https://github.com/BernardoPRocha/agroconecta-secure/actions/runs/44182464009
- Validação posterior do CI: https://github.com/BernardoPRocha/agroconecta-secure/actions/runs/44199638937
- Docker Hub: https://hub.docker.com/r/bernardoprocha/agroconecta-mvp
- Site validado (OFFLINE enquanto VM desalocada): https://agroconecta-bernardo-gs2026.brazilsouth.cloudapp.azure.com

## O que foi comprovado

Terraform apply de 11 recursos; CI e deploy aprovados; HTTPS e triagem por IA funcionando; Prometheus target UP; dashboard Grafana; alerta Normal/Pending/Firing/Normal; desligamento da VM.

**Não incluir prints com o token Docker Hub ou com senhas antigas do Grafana.** Este pacote foi selecionado para excluí-los.

**Ponto de atenção:** não foi anexado o JSON original `reports/evidencias-publicas.json`, porque ele está no computador do aluno. O resultado `APROVADO` está registrado em captura real; incluir o JSON posteriormente se desejado. O código do repositório e o CI mostram execução não-root (UID 10001), mas não há captura dedicada de `id -u` na VM. Os módulos GenAI, Maker e RPA/Big Data seguem como integrações pendentes.

**Disponibilidade:** a VM foi desalocada; o URL não estará acessível ao avaliador até reativação e configuração adequada do NSG. Essa é uma limitação importante frente ao critério de URL funcionando. Custos de disco e IP podem continuar sendo cobrados.

**Segurança:** 47 vulnerabilidades HIGH e nenhuma CRITICAL identificadas no relatório Trivy de 17/11/2026; não interpretar CI verde como ausência de riscos.

**Enunciado:** alinhamento conferido contra o resumo de requisitos fornecido pelo grupo, não contra a rubrica oficial integral.
