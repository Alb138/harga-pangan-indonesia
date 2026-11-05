"""Build the DuckDB warehouse (star schema) from the raw PIHPS cache and reference files."""

import json
import logging
from pathlib import Path

import duckdb
import pandas as pd

from pangan.config import (
    END_DATE,
    LEBARAN_WINDOW,
    OUTLIER_RATIO,
    OUTLIER_WINDOW_DAYS,
    SQL_DIR,
    START_DATE,
)
from pangan.transform import commodity_lookup_from_ref, grid_to_long

log = logging.getLogger(__name__)

NATIONAL_PROVINCE_ID = 0


def read_sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


def build_warehouse(raw_dir: Path, ref_dir: Path, db_path: Path) -> None:
    """(Re)create the warehouse from scratch so every build is reproducible."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    for stale in (db_path, db_path.with_name(db_path.name + ".wal")):
        stale.unlink(missing_ok=True)

    commodities = json.loads((raw_dir / "ref_commodities.json").read_text(encoding="utf-8"))
    with duckdb.connect(str(db_path)) as con:
        create_dimensions(con, ref_dir, commodities)
        _load_facts(con, raw_dir, commodity_lookup_from_ref(commodities))
        _load_optional_refs(con, ref_dir)
        con.execute(read_sql("views.sql"))


def create_dimensions(
    con: duckdb.DuckDBPyConnection, ref_dir: Path, commodities: list[dict]
) -> None:
    """Create every table and fill the dimensions; facts and refs are loaded separately."""
    con.execute(read_sql("schema.sql"))
    _load_dim_date(con, ref_dir)
    _load_dim_province(con, ref_dir)
    _load_dim_commodity(con, commodities)


def _load_dim_date(con: duckdb.DuckDBPyConnection, ref_dir: Path) -> None:
    holidays = pd.read_csv(ref_dir / "holidays.csv", parse_dates=["idul_fitri"])
    holidays["idul_fitri"] = holidays["idul_fitri"].dt.date
    con.register("stg_holidays", holidays)
    params = {
        "start": START_DATE,
        "end": END_DATE,
        "win_lo": LEBARAN_WINDOW[0],
        "win_hi": LEBARAN_WINDOW[1],
    }
    con.execute(read_sql("dim_date.sql"), params)
    con.unregister("stg_holidays")


def _load_dim_province(con: duckdb.DuckDBPyConnection, ref_dir: Path) -> None:
    provinces = pd.read_csv(ref_dir / "provinces.csv")
    con.register("stg_provinces", provinces)
    con.execute(
        """
        INSERT INTO dim_province
        SELECT pihps_id, province_name, bps_code, island_group, tz_region,
               capital, lat, lon, FALSE
        FROM stg_provinces
        """
    )
    con.execute(
        "INSERT INTO dim_province (province_id, province_name, is_national) VALUES (?, ?, TRUE)",
        [NATIONAL_PROVINCE_ID, "Indonesia (Nasional)"],
    )
    con.unregister("stg_provinces")


def _load_dim_commodity(con: duckdb.DuckDBPyConnection, commodities: list[dict]) -> None:
    categories = {c["id"]: c["name"].strip() for c in commodities if c["id"].startswith("cat_")}
    rows = [
        (c["id"], c["name"].strip(), c["cat_id"], categories[c["cat_id"]], c["denomination"])
        for c in commodities
        if c["id"].startswith("com_")
    ]
    con.executemany("INSERT INTO dim_commodity VALUES (?, ?, ?, ?, ?)", rows)


def _cache_file_keys(path: Path) -> tuple[int, int]:
    """'pt3/provnational/2024.json' -> (market_type_id=3, province_id=0)."""
    market_type_id = int(path.parent.parent.name.removeprefix("pt"))
    province = path.parent.name.removeprefix("prov")
    province_id = NATIONAL_PROVINCE_ID if province == "national" else int(province)
    return market_type_id, province_id


def _load_facts(con: duckdb.DuckDBPyConnection, raw_dir: Path, lookup: dict[str, str]) -> None:
    paths = sorted(raw_dir.glob("pt*/prov*/*.json"))
    if not paths:
        raise FileNotFoundError(f"no cached PIHPS files in {raw_dir}; run `pangan extract` first")
    frames = []
    for path in paths:
        market_type_id, province_id = _cache_file_keys(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        frames.append(
            grid_to_long(
                payload,
                province_id=province_id,
                market_type_id=market_type_id,
                commodity_lookup=lookup,
            )
        )
    stg_price = pd.concat(frames, ignore_index=True)
    log.info("loading %d price rows from %d cache files", len(stg_price), len(frames))
    con.register("stg_price", stg_price)
    params = {"ratio": OUTLIER_RATIO, "window_days": OUTLIER_WINDOW_DAYS}
    con.execute(read_sql("load_fact.sql"), params)
    con.unregister("stg_price")


def _load_optional_refs(con: duckdb.DuckDBPyConnection, ref_dir: Path) -> None:
    """UMP and basket come from BPS; the price warehouse still builds without them."""
    for table, filename, columns in [
        ("ref_ump", "ump.csv", "bps_code, year, ump_idr"),
        ("ref_basket", "basket.csv", "commodity_id, qty_kg_per_capita_week"),
    ]:
        path = ref_dir / filename
        if not path.exists():
            log.warning("%s missing: %s stays empty", path, table)
            continue
        con.register("stg_ref", pd.read_csv(path))
        con.execute(f"INSERT INTO {table} SELECT {columns} FROM stg_ref")
        con.unregister("stg_ref")
