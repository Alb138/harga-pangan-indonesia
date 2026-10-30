"""Parsing PIHPS strings and reshaping the wide grid into tidy rows."""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from pangan.transform import (
    LONG_COLUMNS,
    commodity_lookup_from_ref,
    grid_to_long,
    parse_grid_date,
    parse_price,
)

FIXTURE = Path(__file__).parent / "fixtures" / "grid_sample.json"
LOOKUP = {"Beras Kualitas Bawah I": "com_1", "Cabai Merah Keriting": "com_14"}


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("16,150", 16150),
        ("1,234,567", 1234567),
        (" 16,150 ", 16150),
        ("950", 950),
        ("-", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_price_cases(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", ["16.150,5", "abc", "16,15", "1,6150"])
def test_parse_price_rejects_unknown_formats(raw):
    with pytest.raises(ValueError):
        parse_price(raw)


def test_parse_grid_date_day_first():
    assert parse_grid_date("01/03/2024") == date(2024, 3, 1)


def test_grid_to_long_shape():
    df = grid_to_long(load_fixture(), province_id=13, market_type_id=1, commodity_lookup=LOOKUP)
    assert list(df.columns) == LONG_COLUMNS
    assert len(df) == 3  # 2 commodities x 2 days, minus one "-"
    assert set(df["commodity_id"]) == {"com_1", "com_14"}
    assert df["province_id"].dtype == "int32"
    assert df["market_type_id"].dtype == "int8"
    assert df["price_idr"].dtype == "int64"
    assert pd.api.types.is_datetime64_any_dtype(df["date_key"])
    first = df[(df["commodity_id"] == "com_1")].iloc[0]
    assert first["date_key"] == pd.Timestamp("2024-03-01")
    assert first["price_idr"] == 15050


def test_grid_to_long_strips_names():
    df = grid_to_long(load_fixture(), province_id=0, market_type_id=4, commodity_lookup=LOOKUP)
    cabai = df[df["commodity_id"] == "com_14"].sort_values("date_key")
    assert cabai["price_idr"].tolist() == [66800, 1234567]
    assert (df["province_id"] == 0).all()


def test_grid_to_long_empty():
    df = grid_to_long({"data": []}, province_id=33, market_type_id=1, commodity_lookup=LOOKUP)
    assert df.empty
    assert list(df.columns) == LONG_COLUMNS
    assert df["price_idr"].dtype == "int64"


def test_grid_to_long_unknown_name_raises():
    payload = {"data": [{"no": 1, "name": "Garam Dapur", "level": 2, "01/03/2024": "5,000"}]}
    with pytest.raises(KeyError):
        grid_to_long(payload, province_id=13, market_type_id=1, commodity_lookup=LOOKUP)


def test_commodity_lookup_from_ref():
    ref = [
        {"id": "cat_7", "name": "Cabai Merah", "cat_id": None},
        {"id": "com_14", "name": "Cabai Merah Keriting ", "cat_id": "cat_7"},
    ]
    assert commodity_lookup_from_ref(ref) == {"Cabai Merah Keriting": "com_14"}
