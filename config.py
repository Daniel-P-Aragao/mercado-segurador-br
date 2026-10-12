import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SEEDS_DIR = ROOT / "seeds"

SES_URL = "https://www2.susep.gov.br/redarq.asp?arq=BaseCompleta%2ezip"

GCP_PROJECT = os.getenv("GCP_PROJECT", "")
BQ_DATASET = "susep"
BQ_DATASET_MARTS = "susep_marts"