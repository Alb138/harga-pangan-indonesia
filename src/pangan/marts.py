"""Run the analysis SQL in sql/marts/: one file per business question, creating mart_* tables."""

from pathlib import Path

import duckdb

from pangan.config import HOUSEHOLD_SIZE, SQL_DIR

MART_TABLES = [
    "mart_q1_lebaran_index",
    "mart_q1_summary",
    "mart_q2_weekly",
    "mart_q2_volatility",
    "mart_q2_top_shocks",
    "mart_q3_province_index",
    "mart_q3_disparity",
    "mart_q4_markup",
    "mart_q5_affordability",
]


def build_marts(con: duckdb.DuckDBPyConnection, sql_dir: Path = SQL_DIR / "marts") -> list[str]:
    """Execute the mart files in name order and return the mart tables that now exist."""
    con.execute(f"SET VARIABLE household_size = {int(HOUSEHOLD_SIZE)}")
    for path in sorted(sql_dir.glob("*.sql")):
        con.execute(path.read_text(encoding="utf-8"))
    found = con.execute(
        "SELECT table_name FROM duckdb_tables() WHERE starts_with(table_name, 'mart_') "
        "ORDER BY table_name"
    ).fetchall()
    return [name for (name,) in found]
