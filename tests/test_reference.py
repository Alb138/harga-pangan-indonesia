"""Sanity checks for the hand-curated reference tables in data/reference/."""

import pandas as pd

from pangan.config import REF_DIR

TZ_REGIONS = {"Barat", "Tengah", "Timur"}
ISLAND_GROUPS = {
    "Sumatera",
    "Jawa",
    "Bali-Nusa Tenggara",
    "Kalimantan",
    "Sulawesi",
    "Maluku-Papua",
}


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(REF_DIR / name)


def test_provinces_unique_ids():
    prov = load("provinces.csv")
    assert len(prov) == 34
    assert prov["pihps_id"].is_unique
    assert prov["bps_code"].is_unique


def test_provinces_enums():
    prov = load("provinces.csv")
    assert set(prov["tz_region"]) <= TZ_REGIONS
    assert set(prov["island_group"]) <= ISLAND_GROUPS
    assert prov["lat"].between(-11, 6).all()
    assert prov["lon"].between(95, 141).all()


def test_holidays_one_per_year_2018_2026():
    hol = load("holidays.csv")
    assert list(hol["year"]) == list(range(2018, 2027))
    fitri = pd.to_datetime(hol["idul_fitri"])
    assert (fitri.dt.year == hol["year"]).all()
    assert fitri.is_monotonic_increasing
