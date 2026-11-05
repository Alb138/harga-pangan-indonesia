"""Write the Tableau-ready CSVs: each sql/exports/<name>.sql becomes exports/tableau/<name>.csv."""

from pathlib import Path

import duckdb

from pangan.config import EXPORT_DIR, SQL_DIR

EXPORT_SQL_DIR = SQL_DIR / "exports"
EXPORT_FILES = [
    "lebaran_index.csv",
    "lebaran_summary.csv",
    "weekly_national.csv",
    "volatility.csv",
    "top_shocks.csv",
    "province_index.csv",
    "disparity_trend.csv",
    "supply_chain_markup.csv",
    "affordability.csv",
    "price_weekly_province.csv",
]


def export_tableau(con: duckdb.DuckDBPyConnection, out_dir: Path = EXPORT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for filename in EXPORT_FILES:
        query = (EXPORT_SQL_DIR / filename.replace(".csv", ".sql")).read_text(encoding="utf-8")
        path = out_dir / filename
        target = path.as_posix().replace("'", "''")  # SQL string literal: double any quote
        con.execute(f"COPY ({query.strip().rstrip(';')}) TO '{target}' (HEADER)")
        written.append(path)
    return written
