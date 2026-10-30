"""The five analysis marts, checked against hand-computed numbers on a synthetic warehouse."""

from datetime import date

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
        SELECT median_peak_pct, median_peak_t, median_start_rise_t, median_recover_t, n_years
        FROM mart_q1_summary WHERE commodity_id = 'com_1'
        """,
    )
    assert summary[0] == pytest.approx(0.20)
    assert summary[1:] == (-7, -10, 12, 1)


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
