# Trivy - registro preliminar de riscos

Data: 17/11/2026

Imagem local: agroconecta-mvp:headless
Sistema: Debian 13.7

Resultados observados:
- 47 vulnerabilidades HIGH.
- 0 vulnerabilidades CRITICAL.
- 0 vulnerabilidades com correcao disponivel segundo Trivy 0.70.0 com --ignore-unfixed.
- Nenhum alerta Python encontrado no resumo.

Mitigacoes verificadas:
- Container sem root (UID 10001).
- Filesystem de execucao somente leitura.
- Capacidades Linux removidas.
- Restricao no-new-privileges.
- Modelo ACV carregado e inferencia real aprovada.

Os 47 alertas HIGH permanecem abertos.
A ausencia de patch nao comprova ausencia de explorabilidade.

O pipeline preservara o relatorio completo e bloqueara
vulnerabilidades criticas e vulnerabilidades corrigiveis.

A implantacao publica depende de revisao e aceite
explicito dos riscos restantes.