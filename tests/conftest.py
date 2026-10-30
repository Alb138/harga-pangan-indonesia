"""Shared fixtures: a miniature raw cache + reference folder that build_warehouse can load."""

import json
import shutil
from pathlib import Path

import pytest

from pangan.config import REF_DIR

MARCH_DAYS = ["01/03/2024", "04/03/2024", "05/03/2024", "06/03/2024", "07/03/2024"]

REF_COMMODITIES = [
    {"id": "cat_1", "name": "Beras", "cat_id": None, "denomination": "kg"},
    {"id": "com_1", "name": "Beras Kualitas Bawah I", "cat_id": "cat_1", "denomination": "kg"},
    {"id": "cat_7", "name": "Cabai Merah", "cat_id": None, "denomination": "kg"},
    {"id": "com_14", "name": "Cabai Merah Keriting ", "cat_id": "cat_7", "denomination": "kg"},
]

PROVINCES_CSV = """\
pihps_id,province_name,bps_code,island_group,tz_region,capital,lat,lon,valid_from_year
13,DKI Jakarta,31,Jawa,Barat,Jakarta,-6.20,106.85,2018
33,Papua,94,Maluku-Papua,Timur,Jayapura,-2.53,140.72,2018
"""


def grid(rows: dict[str, list[str]]) -> dict:
    """Build a PIHPS-shaped payload: {commodity name: [price per MARCH_DAYS]}."""
    data = [{"no": "I", "name": "Beras", "level": 1, **dict.fromkeys(MARCH_DAYS, "1")}]
    for i, (name, prices) in enumerate(rows.items(), start=1):
        prices_by_day = dict(zip(MARCH_DAYS, prices, strict=True))
        data.append({"no": i, "name": name, "level": 2, **prices_by_day})
    return {"data": data}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def ref_dir(tmp_path) -> Path:
    ref = tmp_path / "reference"
    ref.mkdir()
    (ref / "provinces.csv").write_text(PROVINCES_CSV, encoding="utf-8")
    shutil.copy(REF_DIR / "holidays.csv", ref / "holidays.csv")
    (ref / "ump.csv").write_text("bps_code,year,ump_idr\n31,2024,5067381\n", encoding="utf-8")
    (ref / "basket.csv").write_text(
        "commodity_id,qty_kg_per_capita_week,source\ncom_1,1.5,test\n", encoding="utf-8"
    )
    return ref


@pytest.fixture
def raw_dir(tmp_path) -> Path:
    raw = tmp_path / "raw"
    write_json(raw / "ref_commodities.json", REF_COMMODITIES)
    write_json(raw / "ref_provinces.json", [{"id": 13, "name": "DKI Jakarta"}])
    # DKI traditional market; the last beras price is a 10x typo (150,000 vs 15,000).
    write_json(
        raw / "pt1" / "prov13" / "2024.json",
        grid(
            {
                "Beras Kualitas Bawah I": ["15,000", "15,000", "15,000", "15,000", "150,000"],
                "Cabai Merah Keriting ": ["60,000", "62,000", "-", "64,000", "66,000"],
            }
        ),
    )
    write_json(
        raw / "pt1" / "provnational" / "2024.json",
        grid({"Beras Kualitas Bawah I": ["14,000", "14,000", "14,100", "14,100", "14,200"]}),
    )
    # A province/year with no data at all (Review Focus #2).
    write_json(raw / "pt1" / "prov33" / "2024.json", {"data": []})
    return raw
