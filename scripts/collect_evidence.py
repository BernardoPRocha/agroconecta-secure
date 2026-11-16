"""Record real public HTTP checks without asserting cloud deployment from configuration."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def collect(base):
    parsed = urlparse(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Use a public HTTPS origin without credentials/query')
    base = base.rstrip('/')
    checks=[]
    for path, expected in [('/',200),('/ready',200),('/visao/',200),('/visao/health',200),('/metrics',404)]:
        try:
            with urlopen(base+path,timeout=30) as r:
                status=r.status;body=r.read(100000).decode(errors='replace')
        except HTTPError as e:
            status=e.code;body=e.read(1000).decode(errors='replace')
        checks.append({'path':path,'status':status,'expected':expected,'passed':status==expected,'body_excerpt':body[:400]})
    raw=(Path(__file__).resolve().parents[1]/'examples/0_aparencia_saudavel_1.jpg').read_bytes()
    boundary='agroconecta-evidence-boundary'
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="leaf.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
    req=Request(base+'/visao/api/predict',data=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'},method='POST')
    with urlopen(req,timeout=60) as r:
        prediction=json.load(r)
    ok=all(x['passed'] for x in checks) and bool(prediction.get('detections'))
    return {'timestamp':datetime.now(timezone.utc).isoformat(),'url':base,'checks':checks,'prediction':prediction,'passed':ok}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try: result=collect(args.url)
    except Exception as exc: result={'passed':False,'error':str(exc),'url':args.url,'timestamp':datetime.now(timezone.utc).isoformat()}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print('APROVADO' if result['passed'] else 'FALHOU: confira o JSON gerado')
    raise SystemExit(0 if result['passed'] else 1)
