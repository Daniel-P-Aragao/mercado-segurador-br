import os
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

SES_URL = "https://www2.susep.gov.br/redarq.asp?arq=BaseCompleta%2ezip"

GCP_PROJECT = os.getenv("GCP_PROJECT", "")
BQ_DATASET_RAW = "susep_raw"