"""Data-quality summary of the warehouse: volume, key integrity, outliers, coverage."""

import duckdb

from pangan.config import SQL_DIR

DUPLICATE_KEYS_SQL = """
SELECT COUNT(*) FROM (
    SELECT 1 FROM fact_price_daily
    GROUP BY date_key, province_id, commodity_id, market_type_id
    HAVING COUNT(*) > 1
)
"""


def quality_report(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    def scalar(sql: str) -> int:
        return con.execute(sql).fetchone()[0]

    return {
        "rows": scalar("SELECT COUNT(*) FROM fact_price_daily"),
        "duplicate_keys": scalar(DUPLICATE_KEYS_SQL),
        "null_prices": scalar("SELECT COUNT(*) FROM fact_price_daily WHERE price_idr IS NULL"),
        "outliers": scalar("SELECT COUNT(*) FROM fact_price_daily WHERE is_outlier"),
        "coverage": con.execute((SQL_DIR / "coverage.sql").read_text(encoding="utf-8")).df(),
    }
