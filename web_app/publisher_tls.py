"""Complete a publisher's missing intermediate chain without disabling TLS checks."""
from functools import lru_cache
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

import requests


@lru_cache(maxsize=1)
def _camara_bundle() -> str:
    intermediate = Path(__file__).resolve().parents[1] / "data/publisher_ca/sectigo-public-server-ov-r36.pem"
    with tempfile.NamedTemporaryFile(prefix="clipping-camara-ca-", suffix=".pem", delete=False) as output:
        output.write(Path(requests.certs.where()).read_bytes())
        output.write(b"\n")
        output.write(intermediate.read_bytes())
        return output.name


def publisher_verify(url: str) -> bool | str:
    host = (urlsplit(url).hostname or "").lower()
    return _camara_bundle() if host == "camara.rio" or host.endswith(".camara.rio") else True
