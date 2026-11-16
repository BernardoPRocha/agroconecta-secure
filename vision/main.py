import io, json, logging, os, threading, time, warnings
from contextlib import asynccontextmanager
from pathlib import Path
from PIL import Image, UnidentifiedImageError, ImageOps
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

ROOT=Path(__file__).resolve().parents[1]
LABELS=['Folha de tomate — aparência saudável','Possível pinta-preta','Possível requeima']
EXPECTED=['tomate_saudavel','pinta_preta','requeima']
LIMIT=8*1024*1024
Image.MAX_IMAGE_PIXELS=16_000_000
lock=threading.Lock()
log=logging.getLogger('agroconecta')

@asynccontextmanager
async def lifespan(app):
    app.state.model=None; app.state.imgsz=640
    path=Path(os.environ.get('MODEL_PATH',str(ROOT/'models/best.pt')))
    if path.is_file():
        try:
            import torch
            from ultralytics import YOLO
            torch.set_num_threads(int(os.environ.get('TORCH_THREADS','2')))
            model=YOLO(str(path))
            if [model.names[i] for i in range(len(model.names))]!=EXPECTED:
                raise ValueError('Classes differ from the expected trained tomato detector')
            app.state.model=model
            meta=path.with_name('metadata.json')
            if meta.exists(): app.state.imgsz=json.loads(meta.read_text())['imgsz']
        except Exception:
            log.exception('Could not load tomato detector')
    yield

app=FastAPI(title='AgroConecta ACV',version='1.0.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'vision/static'),name='static')

@app.get('/')
def home(): return FileResponse(ROOT/'vision/static/index.html')

@app.get('/health')
def health():
    return {'status':'ok','model_ready':getattr(app.state,'model',None) is not None}

@app.get('/ready')
def ready():
    if getattr(app.state,'model',None) is None: raise HTTPException(503,'Modelo treinado indisponível.')
    return {'ready':True}

def decode(raw):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as im:
                if im.format not in {'JPEG','PNG','WEBP'}: raise ValueError('Unsupported image')
                im.load(); return ImageOps.exif_transpose(im).convert('RGB')
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise HTTPException(415,'Use uma imagem JPEG, PNG ou WEBP válida, com até 16 milhões de pixels.')

def infer(im,conf):
    start=time.perf_counter()
    # One inference at a time: model predictors share mutable state.
    with lock:
        result=app.state.model.predict(im,conf=conf,imgsz=app.state.imgsz,device='cpu',verbose=False,max_det=30)[0]
    detections=[]
    for b in result.boxes:
        cls=int(b.cls.item())
        detections.append({'class_id':cls,'label':LABELS[cls],
                           'confidence':round(float(b.conf.item()),4),
                           'bbox':[round(float(v),1) for v in b.xyxy[0].tolist()]})
    return {'width':im.width,'height':im.height,'detections':detections,
            'status':'detections' if detections else 'inconclusive',
            'latency_ms':round((time.perf_counter()-start)*1000,1),
            'notice':'Triagem visual experimental. Confiança não é probabilidade clínica. Ausência de detecção não confirma saúde.'}

@app.post('/api/predict')
async def predict(file:UploadFile=File(...),confidence:float=Query(.4,ge=.05,le=.95)):
    if getattr(app.state,'model',None) is None:
        raise HTTPException(503,'Modelo indisponível. Execute o treinamento e reinicie a aplicação.')
    try: raw=await file.read(LIMIT+1)
    finally: await file.close()
    if len(raw)>LIMIT: raise HTTPException(413,'Imagem maior que 8 MB.')
    im=await run_in_threadpool(decode,raw)
    try: return await run_in_threadpool(infer,im,confidence)
    except HTTPException: raise
    except Exception:
        log.exception('Inference failed')
        raise HTTPException(500,'Falha na análise. Tente outra imagem.')
