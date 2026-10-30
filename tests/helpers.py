"""Synthetic warehouse shared by the mart and export tests (hand-checkable numbers)."""

from datetime import date, timedelta

import duckdb

from pangan.config import REF_DIR
from pangan.warehouse import create_dimensions, read_sql

COMMODITIES = [
    {"id": "cat_1", "name": "Beras", "cat_id": None, "denomination": "kg"},
    {"id": "com_1", "name": "Beras Kualitas Bawah I", "cat_id": "cat_1", "denomination": "kg"},
    {"id": "cat_3", "name": "Daging Sapi", "cat_id": None, "denomination": "kg"},
    {"id": "com_9", "name": "Daging Sapi Kualitas 2", "cat_id": "cat_3", "denomination": "kg"},
    {"id": "cat_7", "name": "Cabai Merah", "cat_id": None, "denomination": "kg"},
    {"id": "com_14", "name": "Cabai Merah Keriting", "cat_id": "cat_7", "denomination": "kg"},
]
NATIONAL, DKI, SULSEL, PAPUA = 0, 13, 26, 33
TRADITIONAL, MODERN, WHOLESALE, PRODUCER = 1, 2, 3, 4
LEBARAN_2024 = date(2024, 4, 10)


def build_synthetic_warehouse() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    create_dimensions(con, REF_DIR, COMMODITIES)
    prices: list[tuple] = []

    def add(day: date, province: int, commodity: str, market: int, price: int) -> None:
        prices.append((day, province, commodity, market, price, False))

    # Q1: national beras around Lebaran 2024 — flat 100 baseline, rise to 120 at H-7.
    for t in range(-60, -45):
        add(LEBARAN_2024 + timedelta(days=t), NATIONAL, "com_1", TRADITIONAL, 100)
    add(LEBARAN_2024 + timedelta(days=-20), NATIONAL, "com_1", TRADITIONAL, 104)
    add(LEBARAN_2024 + timedelta(days=-10), NATIONAL, "com_1", TRADITIONAL, 106)
    add(LEBARAN_2024 + timedelta(days=-7), NATIONAL, "com_1", TRADITIONAL, 120)
    add(LEBARAN_2024 + timedelta(days=5), NATIONAL, "com_1", TRADITIONAL, 110)
    add(LEBARAN_2024 + timedelta(days=12), NATIONAL, "com_1", TRADITIONAL, 103)

    # Q2: national beef, one price per Monday, +50% in the fifth week.
    for week, price in enumerate([100, 100, 100, 100, 150]):
        add(date(2024, 1, 1) + timedelta(weeks=week), NATIONAL, "com_9", TRADITIONAL, price)

    # Q4: national chilli along the supply chain, March 2024.
    for market, price in [(PRODUCER, 10_000), (WHOLESALE, 12_000), (TRADITIONAL, 15_000)]:
        add(date(2024, 3, 5), NATIONAL, "com_14", market, price)
    add(date(2024, 3, 5), NATIONAL, "com_14", MODERN, 16_500)

    # Q3 + Q5: province-level traditional-market prices, March 2024.
    add(date(2024, 3, 5), DKI, "com_1", TRADITIONAL, 10_000)
    add(date(2024, 3, 5), DKI, "com_14", TRADITIONAL, 20_000)
    add(date(2024, 3, 5), SULSEL, "com_1", TRADITIONAL, 12_000)
    add(date(2024, 3, 5), SULSEL, "com_14", TRADITIONAL, 20_000)  # no UMP for Sulsel
    add(date(2024, 3, 5), PAPUA, "com_1", TRADITIONAL, 20_000)
    add(date(2024, 4, 2), DKI, "com_1", TRADITIONAL, 10_000)  # April: chilli missing

    con.executemany("INSERT INTO fact_price_daily VALUES (?, ?, ?, ?, ?, ?)", prices)
    con.execute("INSERT INTO ref_basket VALUES ('com_1', 1.0), ('com_14', 0.5)")
    con.execute("INSERT INTO ref_ump VALUES (31, 2024, 3466667)")  # DKI only
    con.execute(read_sql("views.sql"))
    return con
