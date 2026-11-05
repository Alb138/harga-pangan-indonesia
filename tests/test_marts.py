"""The five analysis marts, checked against hand-computed numbers on a synthetic warehouse."""

from datetime import date, timedelta

import pytest

from pangan.marts import MART_TABLES, build_marts
from tests.helpers import DKI, PAPUA, SULSEL, build_synthetic_warehouse


@pytest.fixture(scope="module")
def con():
    connection = build_synthetic_warehouse()
    build_marts(connection)
    yield connection
    connection.close()


def rows(con, sql: str) -> list[tuple]:
    return con.execute(sql).fetchall()


def test_all_marts_run(con):
    assert len(MART_TABLES) == 9
    assert build_marts(con) == sorted(MART_TABLES)


def test_q1_baseline_and_peak(con):
    index_at = dict(
        rows(con, "SELECT t, price_index FROM mart_q1_lebaran_index WHERE commodity_id = 'com_1'")
    )
    assert index_at[-7] == pytest.approx(1.2)
    baseline = [v for t, v in index_at.items() if -60 <= t <= -46]
    assert sum(baseline) / len(baseline) == pytest.approx(1.0)

    (summary,) = rows(
        con,
        """
        SELECT median_peak_pct, peak_week, start_rise_week, recover_week, n_years
        FROM mart_q1_summary WHERE commodity_id = 'com_1'
        """,
    )
    assert summary[0] == pytest.approx(0.20)
    # weeks relative to Lebaran: -1 = H-7..H-1, 0 = H..H+6
    # t=-10 (+6%) -> week -2, t=-7 (+20%) -> week -1, t=12 (+3%) -> week 1
    assert summary[1:] == (-1, -2, 1, 1)


def test_q1_timing_read_from_typical_season():
    """Timing comes from one curve (weekly median across years), so it is always coherent."""
    import duckdb

    from pangan.config import REF_DIR
    from pangan.warehouse import create_dimensions, read_sql
    from tests.helpers import COMMODITIES, NATIONAL, TRADITIONAL

    lebaran = {2023: date(2023, 4, 22), 2024: date(2024, 4, 10), 2025: date(2025, 3, 31)}
    # index in week -2, -1, 0 for each year; baseline = 100
    seasons = {2023: (140, 100, 100), 2024: (100, 130, 100), 2025: (110, 120, 100)}
    con = duckdb.connect()
    create_dimensions(con, REF_DIR, COMMODITIES)
    prices = []
    for year, day0 in lebaran.items():
        for t in range(-60, -45):
            prices.append((day0 + timedelta(days=t), NATIONAL, "com_1", TRADITIONAL, 100, False))
        for t, price in zip((-14, -7, 0), seasons[year], strict=True):
            prices.append((day0 + timedelta(days=t), NATIONAL, "com_1", TRADITIONAL, price, False))
    con.executemany("INSERT INTO fact_price_daily VALUES (?, ?, ?, ?, ?, ?)", prices)
    con.execute(read_sql("views.sql"))
    build_marts(con)

    (summary,) = rows(
        con,
        "SELECT median_peak_pct, peak_week, start_rise_week, recover_week, n_years "
        "FROM mart_q1_summary",
    )
    # yearly peaks 40%, 30%, 20% -> median 30%; typical curve: wk-2 1.10, wk-1 1.20, wk0 1.00
    assert summary[0] == pytest.approx(0.30)
    assert summary[1:] == (-1, -2, 0, 3)


def test_q2_four_week_jump(con):
    (last,) = rows(
        con,
        "SELECT pct_1w, pct_4w FROM mart_q2_weekly WHERE commodity_id = 'com_9' "
        "AND week = DATE '2024-01-29'",
    )
    assert last == (pytest.approx(0.5), pytest.approx(0.5))
    (top,) = rows(
        con, "SELECT week, pct_4w FROM mart_q2_top_shocks WHERE commodity_id='com_9' AND rank=1"
    )
    assert top == (date(2024, 1, 29), pytest.approx(0.5))
    (vol,) = rows(con, "SELECT year, std_pct_1w FROM mart_q2_volatility WHERE commodity_id='com_9'")
    assert vol[0] == 2024 and vol[1] > 0


def test_q3_index_vs_median(con):
    index_by_province = dict(
        rows(
            con,
            "SELECT province_id, index_vs_median FROM mart_q3_province_index "
            "WHERE commodity_id = 'com_1' AND month = DATE '2024-03-01'",
        )
    )
    assert index_by_province == {
        DKI: pytest.approx(10 / 12),
        SULSEL: pytest.approx(1.0),
        PAPUA: pytest.approx(20 / 12),
    }
    (cv,) = rows(
        con,
        "SELECT cv FROM mart_q3_disparity WHERE commodity_id='com_1' AND month = DATE '2024-03-01'",
    )
    assert cv[0] == pytest.approx(0.37796, rel=1e-4)


def test_q4_markup(con):
    markups = rows(
        con,
        "SELECT from_level, to_level, markup_pct FROM mart_q4_markup "
        "WHERE commodity_id = 'com_14' ORDER BY from_order",
    )
    assert markups == [
        ("Produsen", "Pedagang Besar", pytest.approx(0.20)),
        ("Pedagang Besar", "Pasar Tradisional", pytest.approx(0.25)),
        ("Pasar Tradisional", "Pasar Modern", pytest.approx(0.10)),
    ]


def test_q5_share(con):
    (dki,) = rows(
        con,
        "SELECT basket_cost_idr, ump_idr, share_of_ump FROM mart_q5_affordability "
        "WHERE province_id = 13 AND month = DATE '2024-03-01'",
    )
    assert dki[0] == pytest.approx(346_666.67, rel=1e-6)
    assert dki[1] == 3_466_667
    assert dki[2] == pytest.approx(0.10, rel=1e-4)


def test_q5_excludes_incomplete(con):
    kept = rows(con, "SELECT province_id, month FROM mart_q5_affordability ORDER BY ALL")
    # April DKI lacks chilli; Sulsel has no UMP row; Papua lacks chilli.
    assert kept == [(DKI, date(2024, 3, 1))]


def test_q1_peak_tie_resolves_to_earliest_week():
    """Equal (or float-noise-equal) weeks must give the same answer on every run."""
    import duckdb

    from pangan.config import REF_DIR
    from pangan.warehouse import create_dimensions, read_sql
    from tests.helpers import COMMODITIES, NATIONAL, TRADITIONAL

    day0 = date(2024, 4, 10)
    con = duckdb.connect()
    create_dimensions(con, REF_DIR, COMMODITIES)
    prices = [(day0 + timedelta(days=t), NATIONAL, "com_1", TRADITIONAL, 100, False)
              for t in range(-60, -45)]
    # weeks -3 and -2 tie at +10%; float noise below 1e-6 must not break the tie
    for t, price in [(-21, 110), (-14, 110.0000001), (-7, 100)]:
        prices.append((day0 + timedelta(days=t), NATIONAL, "com_1", TRADITIONAL, price, False))
    con.executemany("INSERT INTO fact_price_daily VALUES (?, ?, ?, ?, ?, ?)", prices)
    con.execute(read_sql("views.sql"))
    build_marts(con)
    (peak_week,) = rows(con, "SELECT peak_week FROM mart_q1_summary")[0]
    assert peak_week == -3
