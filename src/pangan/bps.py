"""Read BPS dynamic tables (UMP) into tidy rows.

A BPS dynamic table stores each cell under a key that concatenates its coordinates:
f"{vervar}{var}{turvar}{tahun}{turtahun}" -> value. The same layout is used by the
bps.go.id pages and by the official WebAPI, so one parser serves both.
"""

import re

import pandas as pd

_LEADING_CODE = re.compile(r"\s*(\d{2})\s")


def _bps_code(vervar: dict) -> int:
    """Province code from a row label ('11 Aceh ') or, for older tables, its value (1100)."""
    match = _LEADING_CODE.match(vervar["label"])
    return int(match.group(1)) if match else vervar["val"] // 100


def parse_dynamic_table(payload: dict) -> pd.DataFrame:
    var = payload["var"][0]["val"]
    turvar = payload["turvar"][0]["val"]
    turtahun = payload["turtahun"][0]["val"]
    cells = payload["datacontent"]
    rows = [
        {
            "bps_code": _bps_code(row),
            "year": int(tahun["label"]),
            "value": cells[key],
        }
        for row in payload["vervar"]
        for tahun in payload["tahun"]
        if (key := f"{row['val']}{var}{turvar}{tahun['val']}{turtahun}") in cells
    ]
    return pd.DataFrame(rows, columns=["bps_code", "year", "value"])


def ump_frame(tables: list[dict], bps_codes: set[int]) -> pd.DataFrame:
    """UMP per province and year, limited to the provinces PIHPS reports on."""
    ump = pd.concat([parse_dynamic_table(t) for t in tables], ignore_index=True)
    ump = ump[ump["bps_code"].isin(bps_codes)].rename(columns={"value": "ump_idr"})
    ump["ump_idr"] = ump["ump_idr"].round().astype("int64")
    return ump.sort_values(["bps_code", "year"]).reset_index(drop=True)
