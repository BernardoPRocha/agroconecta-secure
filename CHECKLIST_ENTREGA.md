# Checklist de entrega Secure

## Código preparado nesta revisão
- [x] requirements.txt incluído no contexto Docker; aplicação não-root.
- [x] ACV incorporado, pesos reais, navegação e inferência verificadas localmente.
- [x] Deploy OIDC + Azure Run Command; SSH reservado ao administrador.
- [x] Caddy HTTPS e porta da aplicação sem exposição direta.
- [x] Prometheus interno; Grafana local por túnel; persistência e alerta provisionado.
- [x] Testes de aplicação e configuração; validações disponíveis registradas em reports.

## Execução externa - ainda não comprovada
- [ ] Terraform validate/plan/apply no ambiente autorizado.
- [ ] Repositório Secure público, identity OIDC e environment configurados.
- [ ] Pipeline completo verde: Gitleaks, Semgrep, Trivy e smoke test.
- [ ] URL HTTPS funcionando e câmera no navegador.
- [ ] Docker UID 10001 comprovado na VM.
- [ ] Prometheus UP e dashboard com dados reais.
- [ ] Alerta Firing e recuperação registrados.
- [ ] Evidências e links reais incorporados ao PDF final.
- [ ] Enunciado oficial integral e forma de envio conferidos.

Não substitua evidências externas por este checklist.
