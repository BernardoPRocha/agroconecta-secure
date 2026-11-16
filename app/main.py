"""AgroConecta: portal demonstrativo de integração do Global Solution 2026.2.

ACV integrado; RAG, sensores e cotações permanecem pendentes.
O portal não simula resultados agronômicos como se fossem dados reais.
"""
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from vision.main import app as vision_app, lifespan as vision_lifespan

from datetime import datetime, timezone
from html import escape
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

@asynccontextmanager
async def lifespan(app):
    async with vision_lifespan(vision_app):
        yield


app = FastAPI(
    lifespan=lifespan,
    title="AgroConecta - MVP de integração",
    description="Portal demonstrativo e infraestrutura de Secure DevOps da GS 2026.2",
    version="1.1.0",
)

# Observabilidade real: contagem e duração das chamadas à API.
# O rótulo usa o template da rota, não a URL livre, para evitar cardinalidade excessiva.
REQUEST_COUNT = Counter(
    "http_requests_total", "Total de requisições HTTP",
    ["handler", "method", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "Duração das requisições HTTP em segundos",
    ["handler", "method"], buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

MODULES = {
    "campo": {
        "titulo": "Monitoramento de Campo",
        "responsavel": "Equipe Maker Lab / Big Data",
        "descricao": "Umidade e temperatura da área de cultivo, cruzadas com dados meteorológicos.",
        "proxima_integracao": "Conectar o dispositivo Maker e a coleta Open-Meteo; exibir dados reais e data da leitura.",
    },
    "visao": {
        "titulo": "Triagem de folhas de tomate",
        "responsavel": "Bernardo - Applied Computer Vision",
        "descricao": "Análise experimental de aparência saudável, possível pinta-preta e possível requeima.",
        "proxima_integracao": "ACV integrado em /visao/; limitado a folhas de tomate e triagem experimental.",
    },
    "copiloto": {
        "titulo": "Copiloto Agrícola EMBRAPA",
        "responsavel": "Renato - Generative AI",
        "descricao": "Respostas fundamentadas em documentos técnicos de cultivo.",
        "proxima_integracao": "Conectar o endpoint RAG e apresentar referências e recusa de temas fora do escopo.",
    },
    "cotacoes": {
        "titulo": "Central de Cotações CEASA",
        "responsavel": "Eric - RPA / Big Data",
        "descricao": "Consulta de preços coletados e tratados pelo pipeline de dados.",
        "proxima_integracao": "Conectar a fonte RPA/Big Data, data de coleta, unidade e referência geográfica.",
    },
}


@app.middleware("http")
async def observability(request: Request, call_next):
    inicio = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        rota = request.scope.get("route")
        handler = getattr(rota, "path", None)
        handler = request.scope.get("root_path", "") + handler if handler else "unmatched"
        if request.url.path != "/metrics":
            REQUEST_COUNT.labels(handler=handler, method=request.method, status=str(status)).inc()
            REQUEST_DURATION.labels(handler=handler, method=request.method).observe(perf_counter() - inicio)


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "AgroConecta - Portal Secure DevOps",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/status")
def integration_status():
    return {
        "projeto": "AgroConecta",
        "tipo": "MVP demonstrativo de integração",
        "ods": ["ODS 2", "ODS 13"],
        "secure_devops": {"status": "portal_em_execucao", "producao_azure": "a_confirmar_no_deploy"},
        "modulos": {
            chave: {"responsavel": modulo["responsavel"], "status": ("integrado" if chave == "visao" else "integracao_pendente")}
            for chave, modulo in MODULES.items()
        },
    }


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


STYLE = """
<style>
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, 'Segoe UI', Arial, sans-serif; background:#f2f7f3;
       color:#193026; margin:0; line-height:1.55; }
.container { max-width:1050px; margin:auto; padding:26px 18px; }
header { background:linear-gradient(115deg,#14532d,#15803d); color:white; border-radius:16px;
         padding:28px; margin-bottom:24px; }
h1 { margin:0 0 8px; font-size:clamp(1.5rem,3vw,2.2rem); }
header p { margin:0; }
.note { padding:13px 16px; border:1px solid #a7d6ad; background:#eef9ed; border-radius:10px;
        margin:0 0 20px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(225px,1fr)); gap:16px; }
.card { display:block; text-decoration:none; background:white; border:1px solid #d7e6d9; border-top:4px solid #16a34a;
        padding:20px; border-radius:12px; color:#193026; }
.card:hover,.card:focus-visible { outline:2px solid #15803d; outline-offset:2px; }
.tag { display:inline-block; padding:4px 9px; background:#fff1cf; color:#764a05; font-size:.78rem;
       font-weight:650; border-radius:30px; }
h2 { font-size:1.15rem; margin:14px 0 6px; }
p { margin:8px 0; }
footer { font-size:.88rem; color:#496155; padding:22px 0; }
a { color:#146c38; }
.back { display:inline-block; margin:20px 0; }
</style>
"""


def page(content: str) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>AgroConecta - MVP</title>" + STYLE + "</head><body><main class='container'>"
        + content + "</main></body></html>"
    )


@app.get("/", response_class=HTMLResponse)
def dashboard():
    cards = "".join(
        f"<a class='card' href='/modulos/{escape(chave)}'>"
        f"<span class='tag'>{'ACV integrado' if chave == 'visao' else 'Integração pendente'}</span>"
        f"<h2>{escape(modulo['titulo'])}</h2>"
        f"<p>{escape(modulo['descricao'])}</p>"
        f"<p><strong>Ver detalhes do módulo</strong></p></a>"
        for chave, modulo in MODULES.items()
    )
    return page(
        "<header><h1>AgroConecta</h1>"
        "<p>Inteligência e apoio à decisão para pequenos produtores rurais | ODS 2 e ODS 13</p>"
        "</header><div class='note'><strong>Portal demonstrativo:</strong> o ACV está conectado ao modelo real. Esta entrega inclui a camada "
        "web/DevOps. Dados de sensores, RAG e cotações só serão exibidos após "
        "as integrações reais serem conectadas e testadas.</div>"
        f"<section class='grid' aria-label='Módulos do AgroConecta'>{cards}</section>"
        "<footer>Global Solution 2026.2 | Verificação: <a href='/health'>/health</a> | "
        "<a href='/api/status'>/api/status</a> | <a href='/metrics'>/metrics</a></footer>"
    )


@app.get("/modulos/{modulo_id}", response_class=HTMLResponse)
def module_details(modulo_id: str):
    if modulo_id == "visao":
        return RedirectResponse("/visao/", status_code=307)
    modulo = MODULES.get(modulo_id)
    if modulo is None:
        return HTMLResponse("Módulo não encontrado", status_code=404)
    return page(
        "<header><h1>" + escape(modulo["titulo"]) + "</h1>"
        "<p>AgroConecta | demonstração de navegação</p></header>"
        "<div class='note'><strong>Status:</strong> integração pendente. "
        "Ainda não há previsões, laudos ou cotações reais disponíveis nesta tela.</div>"
        "<p><strong>Responsável:</strong> " + escape(modulo["responsavel"]) + "</p>"
        "<p><strong>Objetivo:</strong> " + escape(modulo["descricao"]) + "</p>"
        "<p><strong>Próxima integração:</strong> " + escape(modulo["proxima_integracao"]) + "</p>"
        "<a class='back' href='/'>Voltar ao painel</a>"
    )


@app.get("/ready")
def ready():
    if getattr(vision_app.state, "model", None) is None:
        raise HTTPException(503, "Modelo de visão indisponível")
    return {"ready": True, "acv": "modelo_carregado"}

app.mount("/visao", vision_app)
