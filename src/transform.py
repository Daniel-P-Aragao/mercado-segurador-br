"""Limpa a base SES e gera as tabelas fato e dimensão em data/processed."""
import logging

import pandas as pd

from config import PROCESSED_DIR, RAW_DIR, SEEDS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger(__name__)

ANO_INICIAL = 2014  # quebra estrutural: sinistro_ocorrido substitui sinistro_direto/retido
LEITURA = {"sep": ";", "encoding": "latin-1"}

COLUNAS_FATO = [
    "damesano", "coenti", "coramo",
    "premio_direto", "premio_ganho", "sinistro_ocorrido", "desp_com",
]


def carregar_fato() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "Ses_seguros.csv", decimal=",", usecols=COLUNAS_FATO, **LEITURA)
    log.info("Fato bruto: %s linhas", f"{len(df):,}")
    return df


def limpar_fato(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["damesano"] // 100 >= ANO_INICIAL].copy()
    log.info("Após corte a partir de %s: %s linhas", ANO_INICIAL, f"{len(df):,}")

    nulos = df["coramo"].isna().sum()
    if nulos:
        log.warning("Removendo %s linhas sem código de ramo", nulos)
        df = df.dropna(subset=["coramo"])

    df["coramo"] = df["coramo"].astype(int)
    df["data"] = pd.to_datetime(df["damesano"].astype(str), format="%Y%m")
    return df.drop(columns="damesano")


def limpar_cias() -> pd.DataFrame:
    cias = pd.read_csv(RAW_DIR / "Ses_cias.csv", **LEITURA)
    cias.columns = cias.columns.str.lower()
    cias["noenti"] = cias["noenti"].str.strip()
    cias["ativa"] = ~cias["noenti"].str.contains("INATIVA", case=False)
    return cias[["coenti", "noenti", "ativa"]]


def limpar_ramos() -> pd.DataFrame:
    ramos = pd.read_csv(RAW_DIR / "Ses_ramos.csv", **LEITURA)
    ramos["noramo"] = ramos["noramo"].str.replace(r"^\d+\s*-\s*", "", regex=True).str.strip()
    ramos["cogrupo_ramo"] = ramos["coramo"] // 100

    segmentos = pd.read_csv(SEEDS_DIR / "segmentos_ramos.csv")
    ramos = ramos.merge(segmentos, on="cogrupo_ramo", how="left", validate="many_to_one")

    sem_segmento = sorted(ramos.loc[ramos["segmento"].isna(), "cogrupo_ramo"].unique())
    if sem_segmento:
        raise ValueError(f"Grupos sem segmento no seed: {sem_segmento}")
    return ramos


def validar(fato: pd.DataFrame, cias: pd.DataFrame, ramos: pd.DataFrame) -> None:
    ramos_orfaos = set(fato["coramo"]) - set(ramos["coramo"])
    cias_orfas = set(fato["coenti"]) - set(cias["coenti"])
    log.info("Ramos sem cadastro no período: %s %s", len(ramos_orfaos), sorted(ramos_orfaos)[:10])
    log.info("Seguradoras sem cadastro no período: %s", len(cias_orfas))

    chave = ["data", "coenti", "coramo"]
    duplicadas = fato.duplicated(subset=chave).sum()
    log.info("Linhas duplicadas na chave %s: %s", chave, duplicadas)

    negativos = (fato[["premio_ganho", "sinistro_ocorrido"]] < 0).sum()
    log.info("Valores negativos:\n%s", negativos.to_string())


def salvar(df: pd.DataFrame, nome: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    caminho = PROCESSED_DIR / f"{nome}.parquet"
    df.to_parquet(caminho, index=False)
    log.info("Salvo: %s (%s linhas)", caminho.name, f"{len(df):,}")


if __name__ == "__main__":
    fato = limpar_fato(carregar_fato())
    cias = limpar_cias()
    ramos = limpar_ramos()

    validar(fato, cias, ramos)

    salvar(fato, "fato_seguros")
    salvar(cias, "dim_seguradoras")
    salvar(ramos, "dim_ramos")