"""Perfil completo da base SES: cobertura por ano, natureza dos valores e integridade das chaves."""
import pandas as pd

from config import RAW_DIR

COLUNAS_VALOR = [
    "premio_direto",
    "premio_ganho",
    "sinistro_direto",
    "sinistro_retido",
    "sinistro_ocorrido",
]


def carregar_seguros() -> pd.DataFrame:
    return pd.read_csv(
        RAW_DIR / "Ses_seguros.csv",
        sep=";",
        encoding="latin-1",
        decimal=",",
        usecols=["damesano", "coenti", "coramo", *COLUNAS_VALOR],
    )


def cobertura_por_ano(df: pd.DataFrame) -> pd.DataFrame:
    """Linhas, seguradoras, ramos e % de valores não nulos por ano."""
    df = df.assign(ano=df["damesano"] // 100)
    resumo = df.groupby("ano").agg(
        linhas=("coenti", "size"),
        seguradoras=("coenti", "nunique"),
        ramos=("coramo", "nunique"),
        coramo_max=("coramo", "max"),
    )
    preenchimento = (
        df[COLUNAS_VALOR].ne(0).groupby(df["ano"]).mean().mul(100).round(1).add_prefix("%_")
    )
    return resumo.join(preenchimento)


def teste_acumulado(df: pd.DataFrame, ano: int) -> pd.Series:
    """Prêmio direto total por mês. Se crescer até dezembro e cair em janeiro, é acumulado."""
    recorte = df[df["damesano"] // 100 == ano]
    return recorte.groupby("damesano")["premio_direto"].sum().div(1e9).round(2)


def chaves_orfas(df: pd.DataFrame) -> None:
    cias = pd.read_csv(RAW_DIR / "Ses_cias.csv", sep=";", encoding="latin-1")
    ramos = pd.read_csv(RAW_DIR / "Ses_ramos.csv", sep=";", encoding="latin-1")

    cias_orfas = set(df["coenti"]) - set(cias["Coenti"])
    ramos_orfaos = set(df["coramo"]) - set(ramos["coramo"])
    print(f"Seguradoras sem cadastro: {len(cias_orfas)}")
    print(f"Ramos sem cadastro: {len(ramos_orfaos)} -> exemplos: {sorted(ramos_orfaos)[:15]}")


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", 100)

    seguros = carregar_seguros()
    print(f"Total de linhas: {len(seguros):,}\n")

    print("=== COBERTURA POR ANO ===")
    print(cobertura_por_ano(seguros))

    for ano in (2024, 2025):
        print(f"\n=== PRÊMIO DIRETO POR MÊS, {ano} (R$ bilhões) ===")
        print(teste_acumulado(seguros, ano))

    print("\n=== INTEGRIDADE DAS CHAVES ===")
    chaves_orfas(seguros)