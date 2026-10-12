"""Carrega as tabelas limpas (parquet) no BigQuery e confere a contagem de linhas."""
import logging

import pandas as pd
import pandas_gbq

from config import BQ_DATASET, GCP_PROJECT, PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)

TABELAS = ["fato_seguros", "dim_seguradoras", "dim_ramos"]


def carregar(nome: str) -> int:
    df = pd.read_parquet(PROCESSED_DIR / f"{nome}.parquet")

    schema = None
    if "data" in df.columns:
        df["data"] = df["data"].dt.date
        schema = [{"name": "data", "type": "DATE"}]

    pandas_gbq.to_gbq(
        df,
        destination_table=f"{BQ_DATASET}.{nome}",
        project_id=GCP_PROJECT,
        if_exists="replace",
        table_schema=schema,
    )
    log.info("Enviada: %s (%s linhas)", nome, f"{len(df):,}")
    return len(df)


def conferir(nome: str, esperado: int) -> None:
    consulta = f"SELECT COUNT(*) AS n FROM `{GCP_PROJECT}.{BQ_DATASET}.{nome}`"
    n = pandas_gbq.read_gbq(consulta, project_id=GCP_PROJECT)["n"].iloc[0]
    status = "OK" if n == esperado else "DIVERGENTE"
    log.info("Conferência %s: local=%s, BigQuery=%s -> %s", nome, esperado, n, status)


if __name__ == "__main__":
    if not GCP_PROJECT:
        raise SystemExit("GCP_PROJECT vazio. Confira o arquivo .env.")

    for tabela in TABELAS:
        linhas = carregar(tabela)
        conferir(tabela, linhas)