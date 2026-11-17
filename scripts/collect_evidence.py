"""Record public HTTPS checks without claiming cloud deployment from configuration.

Only the Azure Brazil South VM DNS origin is supported. The collector does not
follow HTTP redirects and rejects arbitrary hosts, IPs, ports and URL paths.
"""

import argparse
import httpx
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

AZURE_DNS_SUFFIX = ".brazilsouth.cloudapp.azure.com"
DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
CHECKS = [
    ("/", 200),
    ("/ready", 200),
    ("/visao/", 200),
    ("/visao/health", 200),
    ("/metrics", 404),
]


def validated_host(origin: str) -> str:
    """Allow only an HTTPS Azure Brazil South public DNS origin."""
    parsed = urlsplit(origin)
    host = parsed.hostname
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.port not in (None, 443)
        or not host.endswith(AZURE_DNS_SUFFIX)
    ):
        raise ValueError("Use somente a origem HTTPS da VM Azure Brazil South")

    label = host[: -len(AZURE_DNS_SUFFIX)]
    if not DNS_LABEL.fullmatch(label):
        raise ValueError("O nome DNS da VM Azure e invalido")
    return host


def https_request(host, path, *, method="GET", data=None, headers=None, timeout=30, max_bytes=100000):
    """Verified HTTPS, no proxies/redirects and a bounded response body."""
    host = validated_host(f"https://{host}")
    with httpx.stream(
        method, f"https://{host}{path}", content=data,
        headers=headers or {}, timeout=timeout,
        verify=True, follow_redirects=False, trust_env=False,
    ) as response:
        body = bytearray()
        for chunk in response.iter_bytes(chunk_size=16384):
            body.extend(chunk[:max_bytes - len(body)])
            if len(body) >= max_bytes:
                break
        return response.status_code, bytes(body)

def collect(base):
    host = validated_host(base)
    base = f"https://{host}"
    checks = []
    for path, expected in CHECKS:
        status, data = https_request(host, path)
        excerpt = data.decode("utf-8", errors="replace")[:400]
        checks.append({
            "path": path,
            "status": status,
            "expected": expected,
            "passed": status == expected,
            "body_excerpt": excerpt,
        })

    raw = (Path(__file__).resolve().parents[1] / "examples/0_aparencia_saudavel_1.jpg").read_bytes()
    boundary = "agroconecta-evidence-boundary"
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="leaf.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'.encode()
        + raw
        + f"\r\n--{boundary}--\r\n".encode()
    )
    status, response_body = https_request(
        host,
        "/visao/api/predict",
        method="POST",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=60,
        max_bytes=1_000_000,
    )
    if status != 200:
        raise RuntimeError(f"A API de inferencia retornou HTTP {status}")
    prediction = json.loads(response_body.decode("utf-8"))
    ok = all(check["passed"] for check in checks) and bool(prediction.get("detections"))
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "url": base,
        "checks": checks,
        "prediction": prediction,
        "passed": ok,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = collect(args.url)
    except Exception as exc:
        result = {
            "passed": False,
            "error": str(exc),
            "url": args.url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("APROVADO" if result["passed"] else "FALHOU: confira o JSON gerado")
    raise SystemExit(0 if result["passed"] else 1)


