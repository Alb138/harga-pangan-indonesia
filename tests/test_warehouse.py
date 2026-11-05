"""Building the DuckDB star schema from the raw cache, plus data-quality reporting."""

import duckdb
import pytest

from pangan.quality import quality_report
from pangan.warehouse import build_warehouse

TABLES = {
    "dim_date",
    "dim_province",
    "dim_commodity",
    "dim_market_type",
    "fact_price_daily",
    "ref_ump",
    "ref_basket",
}


@pytest.fixture
def con(raw_dir, ref_dir, tmp_path):
    db_path = tmp_path / "test.duckdb"
    build_warehouse(raw_dir, ref_dir, db_path)
    connection = duckdb.connect(str(db_path), read_only=True)
    yield connection
    connection.close()


def scalar(con, sql: str):
    return con.execute(sql).fetchone()[0]


def test_build_creates_tables_and_rows(con):
    tables = {row[0] for row in con.execute("SELECT table_name FROM duckdb_tables()").fetchall()}
    assert TABLES <= tables
    # DKI: 5 beras + 4 cabai (one "-"); national: 5 beras
    assert scalar(con, "SELECT COUNT(*) FROM fact_price_daily") == 14
    assert scalar(con, "SELECT COUNT(*) FROM ref_ump") == 1
    assert scalar(con, "SELECT COUNT(*) FROM ref_basket") == 1


def test_primary_key_unique(con):
    report = quality_report(con)
    assert report["rows"] == 14
    assert report["duplicate_keys"] == 0
    assert report["null_prices"] == 0


def test_outlier_flagged_and_excluded(con):
    flagged = con.execute(
        "SELECT date_key, price_idr FROM fact_price_daily WHERE is_outlier"
    ).fetchall()
    assert [(str(d), p) for d, p in flagged] == [("2024-03-07", 150000)]
    assert quality_report(con)["outliers"] == 1
    max_beras = "SELECT MAX(price_idr) FROM v_price_province WHERE commodity_id = 'com_1'"
    assert scalar(con, max_beras) == 15000


def test_national_separated(con):
    assert scalar(con, "SELECT COUNT(*) FROM v_price_province WHERE province_id = 0") == 0
    assert scalar(con, "SELECT COUNT(*) FROM v_price_national WHERE province_id = 0") == 5
    assert scalar(con, "SELECT province_name FROM dim_province WHERE is_national") == (
        "Indonesia (Nasional)"
    )


def test_dim_commodity_names_stripped(con):
    assert scalar(con, "SELECT commodity_name FROM dim_commodity WHERE commodity_id='com_14'") == (
        "Cabai Merah Keriting"
    )
    assert scalar(con, "SELECT category_name FROM dim_commodity WHERE commodity_id='com_14'") == (
        "Cabai Merah"
    )


def test_dim_market_type_chain_order(con):
    rows = con.execute("SELECT name FROM dim_market_type ORDER BY chain_order").fetchall()
    chain = ["Produsen", "Pedagang Besar", "Pasar Tradisional", "Pasar Modern"]
    assert [r[0] for r in rows] == chain


def test_dim_date_lebaran(con):
    row = con.execute(
        "SELECT days_to_lebaran, is_ramadan, lebaran_year FROM dim_date WHERE date_key='2024-04-03'"
    ).fetchone()
    assert row == (-7, True, 2024)
    row = con.execute(
        "SELECT days_to_lebaran, is_ramadan FROM dim_date WHERE date_key='2024-01-01'"
    ).fetchone()
    assert row == (None, False)
    assert scalar(con, "SELECT MIN(date_key) FROM dim_date").isoformat() == "2018-01-01"
    assert scalar(con, "SELECT MAX(date_key) FROM dim_date").isoformat() == "2026-09-30"


def test_empty_cache_file_ok(con):
    coverage = quality_report(con)["coverage"]
    papua = coverage[(coverage["province_name"] == "Papua") & (coverage["year"] == 2024)]
    dki = coverage[(coverage["province_name"] == "DKI Jakarta") & (coverage["year"] == 2024)]
    assert papua["pct_business_days"].item() == 0
    assert 0 < dki["pct_business_days"].item() < 0.05  # 5 of ~260 business days


def test_missing_optional_refs_ok(raw_dir, ref_dir, tmp_path):
    (ref_dir / "ump.csv").unlink()
    (ref_dir / "basket.csv").unlink()
    db_path = tmp_path / "no_refs.duckdb"
    build_warehouse(raw_dir, ref_dir, db_path)
    with duckdb.connect(str(db_path), read_only=True) as con:
        assert scalar(con, "SELECT COUNT(*) FROM ref_ump") == 0
        assert scalar(con, "SELECT COUNT(*) FROM ref_basket") == 0


def test_rebuild_is_idempotent(raw_dir, ref_dir, tmp_path):
    db_path = tmp_path / "twice.duckdb"
    build_warehouse(raw_dir, ref_dir, db_path)
    build_warehouse(raw_dir, ref_dir, db_path)
    with duckdb.connect(str(db_path), read_only=True) as con:
        assert scalar(con, "SELECT COUNT(*) FROM fact_price_daily") == 14


def test_no_cache_files_raises_clear_error(raw_dir, ref_dir, tmp_path):
    for path in raw_dir.glob("pt*/prov*/*.json"):
        path.unlink()
    with pytest.raises(FileNotFoundError, match="pangan extract"):
        build_warehouse(raw_dir, ref_dir, tmp_path / "empty.duckdb")


def test_outlier_run_covering_most_of_a_month(ref_dir, tmp_path):
    """A typo repeated for weeks must not become the 'normal' price (seen in PIHPS 2021 data)."""
    from datetime import date

    import pandas as pd

    from tests.conftest import REF_COMMODITIES, write_json

    bad = (date(2024, 3, 4), date(2024, 3, 29))
    days = pd.bdate_range("2024-01-02", "2024-04-30")
    prices = {
        d.strftime("%d/%m/%Y"): "150,000" if bad[0] <= d.date() <= bad[1] else "15,000"
        for d in days
    }
    raw = tmp_path / "raw_run"
    write_json(raw / "ref_commodities.json", REF_COMMODITIES)
    write_json(
        raw / "pt4" / "provnational" / "2024.json",
        {"data": [{"no": 1, "name": "Beras Kualitas Bawah I", "level": 2, **prices}]},
    )
    db_path = tmp_path / "run.duckdb"
    build_warehouse(raw, ref_dir, db_path)

    with duckdb.connect(str(db_path), read_only=True) as con:
        flagged = con.execute(
            "SELECT DISTINCT price_idr FROM fact_price_daily WHERE is_outlier"
        ).fetchall()
        n_flagged = scalar(con, "SELECT COUNT(*) FROM fact_price_daily WHERE is_outlier")
    assert flagged == [(150000,)]
    assert n_flagged == sum(bad[0] <= d.date() <= bad[1] for d in days)
