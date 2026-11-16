from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleAgro',fontName='Helvetica-Bold',fontSize=25,leading=30,textColor=colors.HexColor('#14532d'),spaceAfter=18))
styles.add(ParagraphStyle(name='SectionAgro',fontName='Helvetica-Bold',fontSize=14,leading=18,textColor=colors.HexColor('#14532d'),spaceBefore=15,spaceAfter=10))
styles.add(ParagraphStyle(name='BodyAgro',fontSize=10,leading=15,spaceAfter=10))
styles.add(ParagraphStyle(name='SmallAgro',fontSize=8,leading=11,spaceAfter=6))
story=[]
def p(text,style='BodyAgro'):return Paragraph(text,styles[style])
def add(t,style='BodyAgro'):story.append(p(t,style))
def table(rows,widths):
 t=Table([[p(v,'SmallAgro') for v in row] for row in rows],colWidths=widths,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3efe8')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#ccd9d0'))]))
 story.append(t)
def page():story.append(PageBreak())
add('AgroConecta<br/>Secure DevOps + ACV','TitleAgro')
add('Global Solution 2026.2 | FIAP | Revisão técnica de 16/11/2026','SmallAgro')
add('<b>Responsável:</b> Bernardo Rocha - RM99209<br/><b>Equipe:</b> Eric Rodrigues - RM550249; Renato Izumi - RM99242.')
add('Estado desta entrega','SectionAgro')
add('Código corrigido e integração local do ACV testada. <b>Este documento não comprova implantação na Azure.</b> URL pública, execução do CI/CD, certificado HTTPS e alerta disparado dependem de execução na conta do grupo.')
add('Objetivo e escopo','SectionAgro')
add('Disponibilizar o AgroConecta para apoiar pequenos produtores rurais, com foco nos ODS 2 e 13. O portal integra o detector de folhas de tomate: aparência saudável, possível pinta-preta e possível requeima. RAG, sensores e cotações continuam identificados como pendentes.')
add('Correções realizadas','SectionAgro')
table([['Problema anterior','Correção no pacote'],['requirements.txt excluído do build','Exceção explícita no .dockerignore.'],['SSH do GitHub bloqueado pelo firewall','OIDC e Azure Run Command, mantendo SSH apenas para o administrador.'],['Portal sem ACV','Modelo e interface incorporados em /visao/.'],['HTTP público e métricas expostas','Caddy HTTPS; aplicação interna; /metrics bloqueado no proxy.'],['Alerta manual e configuração não persistente','Regra Grafana provisionada e volumes persistentes.']],[185,310])
page()
add('Arquitetura e segurança','TitleAgro')
add('Fluxo público: navegador → HTTPS / Caddy → FastAPI → detector YOLO em CPU. O portal e o ACV compartilham a mesma origem; isso permite a câmera em contexto HTTPS e evita dependência de CORS entre aplicações.')
table([['Camada','Configuração'],['Aplicação','Processo UID/GID 10001; filesystem somente leitura; /tmp temporário; capabilities removidas; limite de processos, memória e concorrência.'],['Readiness','/ready retorna sucesso apenas se o modelo foi carregado. /health confirma que o processo responde.'],['Rede Azure','80/443 públicos; 22 somente para o CIDR administrativo. Porta 8000 não publicada na VM.'],['CI/CD','Gitleaks, testes, Semgrep, Terraform, build, Trivy e smoke test. Deploy da mesma imagem aprovada, referenciada por digest.'],['Identidade','Federação OIDC restrita ao repositório e ao environment production. Papel Virtual Machine Contributor no escopo de uma VM. Sem chave privada SSH no GitHub.'],['Observabilidade','Prometheus consulta app:8000/metrics. Grafana e Prometheus acessíveis pelo administrador via túnel SSH.']],[115,380])
add('Implantação','SectionAgro')
add('Terraform cria recursos e identidade federada. O workflow autentica na Azure e envia o bundle de configuração via Run Command. Caddy solicita e renova certificados; o domínio deve apontar para a VM e as portas 80/443 precisam estar acessíveis.')
add('A VM padrão foi dimensionada para Standard_B2ms (8 GB), pois o modelo e a observabilidade consomem mais memória que um portal estático. Verificar custo, saldo e cota antes de aplicar. Não houve criação de recursos nesta revisão.')
page()
add('Verificações e limites','TitleAgro')
add('Resultados locais','SectionAgro')
table([['Verificação','Resultado observado'],['Testes Python 3.12','11 testes passaram em 2,30 s; uma advertência de depreciação do ambiente de testes. Log em reports/tests-local.txt.'],['Inferência real','O teste carregou os pesos incluídos e produziu detecções na imagem de exemplo; não foi usada previsão simulada.'],['Tratamento de falhas','Uploads inválidos, tamanho excedido, confiança inválida e ausência de modelo verificados.'],['Configuração e scripts','Payload de deploy e restrições de portas/persistência testados; bash -n e node --check passaram.'],['Terraform','fmt executado; init instalou AzureRM 4.81.0. validate bloqueado pelo ambiente ao abrir socket Unix. Não considerado aprovado.']],[140,355])
add('O que não foi comprovado','SectionAgro')
add('Sem Docker daemon e sem implantação autorizada em uma conta Azure neste ambiente: não foram comprovados build/execução de contêiner, scanners remotos, RBAC/OIDC, certificado emitido, dashboard renderizado, alerta Firing ou URL pública. A configuração do workflow exige validações antes do deploy.')
add('Limites do produto','SectionAgro')
add('As previsões são triagem experimental, não diagnóstico. O modelo suporta folhas de tomate e pode confundir classes ou não detectar folhas. Não houve retreinamento, calibração ou nova validação agronômica nesta revisão. A inferência pública ainda exige avaliação adicional de proteção contra abuso antes de uso produtivo.')
add('Rastreabilidade','SectionAgro')
add('Fonte ACV: github.com/BernardoPRocha/agroconecta-acv<br/>Commit: bf47e285c36955e41b6f676bfc2d5a2c3f311744<br/>Créditos PlantDoc em docs/PLANTDOC_LICENSE.txt e examples/SOURCES.json. Licenciamento Ultralytics: AGPL-3.0 ou comercial.','SmallAgro')
page()
add('Fechamento da entrega','TitleAgro')
add('Evidências a produzir na execução real','SectionAgro')
table([['Etapa','Comprovação necessária'],['1. Infraestrutura','Terraform validate/plan/apply aprovados; recursos Azure e DNS reais.'],['2. Pipeline','Link do run aprovado, incluindo Gitleaks, Semgrep, Trivy, smoke test e deploy.'],['3. Aplicação','URL HTTPS, /ready aprovado e câmera do ACV funcionando no navegador.'],['4. Contêiner','Saída de id -u igual a 10001 na aplicação em execução na VM.'],['5. Monitoramento','Prometheus UP; dashboard com requisições e latência reais.'],['6. Alerta','Parada controlada da aplicação, regra Firing e recuperação para Normal.']],[125,370])
add('Como reproduzir','SectionAgro')
add('O README contém os comandos de instalação, Terraform, configuração de variables/secrets, acesso por túnel e teste do alerta. scripts/collect_evidence.py consulta a URL real, verifica readiness e proteção de métricas e envia uma imagem ao modelo, salvando JSON com o resultado observado.')
add('A regra de disponibilidade é provisionada, avaliada a cada 15 segundos, com espera de 30 segundos. Ausência de dados ou erro na consulta também é tratada como alerta. O pacote não configura envio para destinatários externos; o critério demonstrável é o estado Firing no Grafana.')
add('Critérios e documentação consultada','SectionAgro')
add('Critérios acadêmicos: resumo “Ideia Principal” fornecido pelo grupo. Não houve acesso à rubrica oficial integral. Referências técnicas: documentação oficial de Azure Run Command e OIDC, Caddy Automatic HTTPS, Docker build context e Grafana file provisioning.','SmallAgro')
add('<b>Conclusão:</b> as correções de código estão preparadas e o ACV funciona localmente. A entrega acadêmica só deve ser apresentada como implantada após anexar as evidências externas reais. Nenhuma evidência de nuvem foi fabricada.')

def footer(c,d):
 c.setStrokeColor(colors.HexColor('#ccd9d0'));c.line(50,43,545,43)
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#53695c'))
 c.drawString(50,30,'AgroConecta | Revisão de código e instruções de validação')
 c.drawRightString(545,30,str(d.page))
path=ROOT/'docs/RELATORIO_SECURE_MODELO.pdf'
SimpleDocTemplate(str(path),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=60).build(story,onFirstPage=footer,onLaterPages=footer)
print(path)
