"""Cria as views de negócio (marts) no BigQuery a partir dos arquivos em sql/marts."""
import logging

import pydata_google_auth
from google.cloud import bigquery

from config import BQ_DATASET_MARTS, GCP_PROJECT, ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)

SQL_DIR = ROOT / "sql" / "marts"

# Ordem importa: mart_concentracao lê mart_participacao_anual
VIEWS = ["mart_participacao_anual", "mart_concentracao"]


def cliente() -> bigquery.Client:
    credenciais = pydata_google_auth.get_user_credentials(
        ["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(project=GCP_PROJECT, credentials=credenciais)


def criar_dataset(client: bigquery.Client) -> None:
    dataset = bigquery.Dataset(f"{GCP_PROJECT}.{BQ_DATASET_MARTS}")
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)
    log.info("Dataset pronto: %s", BQ_DATASET_MARTS)


def criar_view(client: bigquery.Client, nome: str) -> None:
    sql = (SQL_DIR / f"{nome}.sql").read_text(encoding="utf-8")
    client.query(sql.format(projeto=GCP_PROJECT)).result()
    log.info("View criada: %s", nome)


if __name__ == "__main__":
    if not GCP_PROJECT:
        raise SystemExit("GCP_PROJECT vazio. Confira o arquivo .env.")

    bq = cliente()
    criar_dataset(bq)
    for view in VIEWS:
        criar_view(bq, view)