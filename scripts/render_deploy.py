"""Build a self-contained Run Command payload from reviewed repository files."""
import base64
import io
import os
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]

def render(image, domain):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*/agroconecta-mvp@sha256:[a-f0-9]{64}", image):
        raise ValueError("Invalid immutable image digest")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.brazilsouth\.cloudapp\.azure\.com", domain):
        raise ValueError("Invalid Azure DNS name")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in ["compose.yml", "Caddyfile"]:
            tar.add(ROOT / "deploy" / name, arcname=name)
        tar.add(ROOT / "monitoring", arcname="monitoring")
        tar.add(ROOT / "scripts/deploy_vm.sh", arcname="deploy_vm.sh")
    payload = base64.b64encode(buf.getvalue()).decode()
    return ("#!/bin/bash\nset -Eeuo pipefail\nmkdir -p /opt/agroconecta\n"
            "base64 -d <<'BUNDLE' | tar -xz -C /opt/agroconecta\n" + payload +
            "\nBUNDLE\nbash /opt/agroconecta/deploy_vm.sh '" + image + "' '" + domain + "'\n")

if __name__ == "__main__":
    Path("deploy-command.sh").write_text(render(os.environ["APP_IMAGE"], os.environ["SITE_DOMAIN"]))
