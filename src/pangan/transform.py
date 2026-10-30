"""Turn PIHPS grid responses (one column per day, prices as text) into tidy rows."""

import re
from datetime import date, datetime

import pandas as pd

LONG_COLUMNS = ["date_key", "province_id", "commodity_id", "market_type_id", "price_idr"]
COMMODITY_LEVEL = 2  # level 1 rows are category averages, which we can recompute ourselves

# "950", "16,150", "1,234,567": digits with comma thousands separators, nothing else.
_PRICE_PATTERN = re.compile(r"\d{1,3}(,\d{3})*")
_MISSING = {"", "-"}


def parse_price(raw: str | None) -> int | None:
    """'16,150' -> 16150; '-' or empty -> None; anything unexpected raises ValueError."""
    if raw is None:
        return None
    text = raw.strip()
    if text in _MISSING:
        return None
    if not _PRICE_PATTERN.fullmatch(text):
        raise ValueError(f"unexpected price format: {raw!r}")
    return int(text.replace(",", ""))


def parse_grid_date(col: str) -> date:
    """PIHPS column headers are day-first: '01/03/2024' is 1 March 2024."""
    return datetime.strptime(col, "%d/%m/%Y").date()


def commodity_lookup_from_ref(ref: list[dict]) -> dict[str, str]:
    """Map stripped commodity names to their `com_*` ids, skipping category rows."""
    return {item["name"].strip(): item["id"] for item in ref if item["id"].startswith("com_")}


def _empty_long() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_key": pd.Series(dtype="datetime64[s]"),
            "province_id": pd.Series(dtype="int32"),
            "commodity_id": pd.Series(dtype="str"),
            "market_type_id": pd.Series(dtype="int8"),
            "price_idr": pd.Series(dtype="int64"),
        }
    )


def grid_to_long(
    payload: dict,
    *,
    province_id: int,
    market_type_id: int,
    commodity_lookup: dict[str, str],
) -> pd.DataFrame:
    """Wide grid -> one row per (date, commodity) with a known price."""
    rows = [row for row in payload["data"] if row["level"] == COMMODITY_LEVEL]
    if not rows:
        return _empty_long()

    wide = pd.DataFrame(rows)
    wide["commodity_id"] = [commodity_lookup[name.strip()] for name in wide["name"]]
    date_cols = [col for col in wide.columns if "/" in col]
    long = wide.melt(
        id_vars="commodity_id", value_vars=date_cols, var_name="day", value_name="raw"
    )
    long["price_idr"] = long["raw"].map(parse_price)
    long = long.dropna(subset=["price_idr"])
    if long.empty:
        return _empty_long()

    day_lookup = {col: parse_grid_date(col) for col in date_cols}
    return pd.DataFrame(
        {
            "date_key": pd.to_datetime(long["day"].map(day_lookup)).astype("datetime64[s]"),
            "province_id": pd.Series(province_id, index=long.index, dtype="int32"),
            "commodity_id": long["commodity_id"].astype("str"),
            "market_type_id": pd.Series(market_type_id, index=long.index, dtype="int8"),
            "price_idr": long["price_idr"].astype("int64"),
        }
    ).reset_index(drop=True)
