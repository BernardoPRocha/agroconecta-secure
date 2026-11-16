from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app, vision_app

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c:
        yield c

def test_health_and_ready_with_real_model(client):
    assert client.get('/health').status_code == 200
    assert client.get('/ready').json()['ready'] is True
    assert client.get('/visao/health').json()['model_ready'] is True

def test_portal_and_vision_navigation(client):
    assert 'ACV integrado' in client.get('/').text
    page = client.get('/modulos/visao')
    assert page.url.path == '/visao/'
    assert './static/' in page.text
    assert client.get('/visao/static/app.js').status_code == 200
    assert "fetch('./health')" in client.get('/visao/static/app.js').text
    assert client.get('/modulos/desconhecido').status_code == 404

def test_other_modules_are_explicitly_pending(client):
    data = client.get('/api/status').json()['modulos']
    assert data['visao']['status'] == 'integrado'
    assert all(data[x]['status'] == 'integracao_pendente' for x in ['campo','copiloto','cotacoes'])

def test_actual_inference_on_example(client):
    data = (ROOT/'examples/0_aparencia_saudavel_1.jpg').read_bytes()
    r = client.post('/visao/api/predict', files={'file':('leaf.jpg',data,'image/jpeg')})
    assert r.status_code == 200
    body = r.json()
    assert body['width'] > 0 and body['height'] > 0
    assert body['detections'], 'Known example should produce detections with bundled model'
    assert all(0 <= d['confidence'] <= 1 and len(d['bbox']) == 4 for d in body['detections'])

def test_invalid_and_oversize_uploads(client):
    assert client.post('/visao/api/predict',files={'file':('x.jpg',b'not an image','image/jpeg')}).status_code == 415
    assert client.post('/visao/api/predict',files={'file':('x.jpg',b'x'*(8*1024*1024+1),'image/jpeg')}).status_code == 413
    assert client.post('/visao/api/predict?confidence=2',files={'file':('x.jpg',b'x','image/jpeg')}).status_code == 422

def test_missing_model_fails_readiness(client,monkeypatch):
    monkeypatch.setattr(vision_app.state,'model',None)
    assert client.get('/health').status_code == 200
    assert client.get('/ready').status_code == 503
    assert client.post('/visao/api/predict',files={'file':('x.jpg',b'x','image/jpeg')}).status_code == 503

def test_metrics_count_vision_requests(client):
    client.get('/visao/health')
    text = client.get('/metrics').text
    assert 'http_requests_total' in text and 'http_request_duration_seconds_bucket' in text
    assert 'handler="/visao/health"' in text
