# Checklist final AgroConecta Secure - 17/11/2026

- [x] Terraform Azure apply: 11 recursos criados (VM Standard_D2s_v4, disco 64 GiB).
- [x] GitHub Actions #11 (tentativa 2): validate e deploy aprovados.
- [x] Gitleaks, Semgrep, pytest, Trivy e smoke test do contêiner no CI.
- [x] HTTPS /ready com modelo carregado e inferência de folhas demonstrada.
- [x] Script collect_evidence.py: APROVADO; JSON original permanece local no computador.
- [x] Prometheus target 1/1 UP; Grafana dashboard com dados reais.
- [x] Teste do alerta: Normal, Pending, Firing e recuperação para Normal.
- [x] VM desalocada após os testes para reduzir custos de processamento.
- [x] Relatório final com prints reais em docs/RELATORIO_FINAL_AGROCONECTA_SECURE.pdf.
- [ ] URL disponível ao avaliador: requer reativar VM e configurar acesso controlado ao NSG.
- [ ] Conferência da rubrica oficial completa da disciplina.
- [ ] Print específico UID 10001 dentro da VM (Dockerfile e CI comprovam comportamento, mas não print específico na VM).
- [ ] Demonstração explícita da câmera do navegador; captura existente comprova upload.
- [ ] Módulos GenAI, Maker e RPA/Big Data ainda pendentes de integração pela equipe.

Riscos: relatório do Trivy registra 47 HIGH, 0 CRITICAL; não alegar ausência de vulnerabilidades.
As capturas com senhas e tokens foram excluídas do pacote.