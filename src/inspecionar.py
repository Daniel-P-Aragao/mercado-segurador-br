"""Perfil rápido dos arquivos principais do SES (colunas, tipos, amostra)."""
import pandas as pd

from config import RAW_DIR

ARQUIVOS = ["Ses_seguros.csv", "Ses_cias.csv", "Ses_ramos.csv", "Ses_campos.csv"]


def ler_amostra(nome: str, n: int = 5) -> pd.DataFrame:
    caminho = RAW_DIR / nome
    for encoding in ("latin-1", "utf-8"):
        try:
            return pd.read_csv(caminho, sep=";", encoding=encoding, nrows=n)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não consegui ler {nome}")


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    for nome in ARQUIVOS:
        tamanho_mb = (RAW_DIR / nome).stat().st_size / 1e6
        df = ler_amostra(nome)
        print(f"\n{'=' * 80}\n{nome}  ({tamanho_mb:.1f} MB)\n{'=' * 80}")
        print("Colunas:", list(df.columns))
        print(df.head())