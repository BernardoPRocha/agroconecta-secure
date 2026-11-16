from pathlib import Path
import importlib.util
import io
import base64
import tarfile
import pytest
import yaml

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render',ROOT/'scripts/render_deploy.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_bundle_has_deploy_and_provisioned_alert():
    result=module.render('bernardo/agroconecta-mvp@sha256:'+'a'*64,'agro-test.brazilsouth.cloudapp.azure.com')
    encoded=result.split("<<'BUNDLE' | tar -xz -C /opt/agroconecta\n")[1].split('\nBUNDLE')[0]
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(encoded)),mode='r:gz') as archive:
        names=archive.getnames()
        assert 'compose.yml' in names
        assert 'monitoring/grafana/provisioning/alerting/availability.yml' in names
        assert not any('.env' in n or n.startswith('/') or '..' in n for n in names)

@pytest.mark.parametrize('image,domain',[
    ('repo/agroconecta-mvp:latest','a.brazilsouth.cloudapp.azure.com'),
    ('repo/agroconecta-mvp@sha256:'+'a'*64,'example.com; touch /tmp/x'),
])
def test_rejects_mutable_images_and_shell_input(image,domain):
    with pytest.raises(ValueError): module.render(image,domain)

def test_internal_ports_and_persistence():
    c=yaml.safe_load((ROOT/'deploy/compose.yml').read_text())
    assert not c['services']['app'].get('ports')
    assert c['services']['app']['read_only']
    for name in ['prometheus','grafana']:
        assert all(x.startswith('127.0.0.1:') for x in c['services'][name]['ports'])
    assert 'grafana_data' in c['volumes']
    alert=yaml.safe_load((ROOT/'monitoring/grafana/provisioning/alerting/availability.yml').read_text())
    assert alert['groups'][0]['rules'][0]['noDataState']=='Alerting'
