"""Parsing BPS dynamic tables (the `datacontent` format shared by the website and WebAPI)."""

import json
from pathlib import Path

from pangan.bps import parse_dynamic_table, ump_frame

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_old_ump_table_codes_from_vervar_value():
    rows = parse_dynamic_table(load("bps_var220_2020.json"))
    assert rows.to_dict("records") == [
        {"bps_code": 11, "year": 2020, "value": 3165031},
        {"bps_code": 31, "year": 2020, "value": 4276350},
        {"bps_code": 94, "year": 2020, "value": 3516700},
    ]


def test_parse_new_ump_table_codes_from_label():
    rows = parse_dynamic_table(load("bps_var2824_2026.json"))
    assert dict(zip(rows["bps_code"], rows["value"], strict=True)) == {
        11: 3932552,
        31: 5729876,
        92: 3766000,
        94: 4436283,
        97: 4508714,
    }
    assert set(rows["year"]) == {2026}


def test_parse_skips_missing_cells():
    payload = load("bps_var220_2020.json")
    del payload["datacontent"]["310022001200"]
    rows = parse_dynamic_table(payload)
    assert 31 not in set(rows["bps_code"])


def test_ump_frame_keeps_pihps_provinces_only():
    tables = [load("bps_var220_2020.json"), load("bps_var2824_2026.json")]
    ump = ump_frame(tables, bps_codes={11, 31, 94})
    assert ump.columns.tolist() == ["bps_code", "year", "ump_idr"]
    assert len(ump) == 6  # 3 provinces x 2 years; new Papua provinces (92, 97) dropped
    assert ump.loc[(ump.bps_code == 94) & (ump.year == 2026), "ump_idr"].item() == 4436283
