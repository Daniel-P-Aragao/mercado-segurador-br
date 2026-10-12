"""Baixa a base completa do SES/SUSEP e extrai os CSVs em data/raw."""
import logging
import zipfile
from pathlib import Path

import requests

from config import RAW_DIR, SES_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)


def baixar_zip(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    log.info("Baixando %s", url)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    return destino


def extrair(zip_path: Path, pasta: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as z:
        nomes = z.namelist()
        log.info("Arquivos no zip: %s", nomes)
        z.extractall(pasta)
    return nomes


if __name__ == "__main__":
    zip_path = baixar_zip(SES_URL, RAW_DIR / "ses_base.zip")
    extrair(zip_path, RAW_DIR)