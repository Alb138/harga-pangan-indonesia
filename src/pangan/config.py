"""Project-wide constants: data period, scraping etiquette, and paths."""

from datetime import date
from pathlib import Path

# --- Data source -----------------------------------------------------------
BASE_URL = "https://www.bi.go.id/hargapangan/WebSite/TabelHarga"
CATEGORY_IDS = [f"cat_{i}" for i in range(1, 11)]

# --- Analysis period -------------------------------------------------------
START_DATE = date(2018, 1, 1)
END_DATE = date(2026, 9, 30)

# --- Polite scraping: sequential requests, pause between them -------------
REQUEST_DELAY_S = 2.0
TIMEOUT_S = 120
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (compatible; harga-pangan-indonesia/0.1; educational portfolio project)"

# --- Analysis assumptions (explained in docs/PENJELASAN.md) ----------------
HOUSEHOLD_SIZE = 4
OUTLIER_RATIO = 3.0
OUTLIER_WINDOW_DAYS = 60
MIN_REPORTING_SHARE = 0.5
LEBARAN_WINDOW = (-90, 45)

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "pihps"
REF_DIR = ROOT / "data" / "reference"
WAREHOUSE_PATH = ROOT / "warehouse" / "pangan.duckdb"
SQL_DIR = ROOT / "sql"
EXPORT_DIR = ROOT / "exports" / "tableau"
FIG_DIR = ROOT / "reports" / "figures"
