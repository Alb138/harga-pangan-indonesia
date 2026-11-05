"""Tableau exports: one readable CSV per dashboard need, names instead of raw ids."""

import pandas as pd
import pytest

from pangan.export import EXPORT_FILES, export_tableau
from pangan.marts import build_marts
from tests.helpers import build_synthetic_warehouse


@pytest.fixture(scope="module")
def exported(tmp_path_factory) -> dict[str, pd.DataFrame]:
    out_dir = tmp_path_factory.mktemp("tableau")
    con = build_synthetic_warehouse()
    build_marts(con)
    paths = export_tableau(con, out_dir)
    con.close()
    assert sorted(p.name for p in paths) == sorted(EXPORT_FILES)
    return {p.name: pd.read_csv(p) for p in paths}


def test_export_files(exported):
    assert len(exported) == 10
    for name, frame in exported.items():
        columns = set(frame.columns)
        assert columns & {"commodity_name", "province_name"}, name
        assert not columns & {"commodity_id", "province_id"}, name


def test_affordability_has_geo_and_share(exported):
    afford = exported["affordability.csv"]
    geo = ["province_name", "tz_region", "island_group", "lat", "lon"]
    assert afford.columns.tolist()[:5] == geo
    (share,) = afford.loc[afford["province_name"] == "DKI Jakarta", "share_of_ump"]
    assert share == pytest.approx(0.10, rel=1e-3)


def test_supply_chain_keeps_step_order(exported):
    steps = exported["supply_chain_markup.csv"].sort_values("from_order")
    assert steps["from_level"].tolist() == ["Produsen", "Pedagang Besar", "Pasar Tradisional"]


def test_weekly_province_prices(exported):
    weekly = exported["price_weekly_province.csv"]
    assert {"week", "avg_price_idr", "tz_region"} <= set(weekly.columns)
    assert (weekly["province_name"] != "Indonesia (Nasional)").all()


def test_export_to_path_with_apostrophe(tmp_path):
    """Folder names like C:/Users/D'Souza must not break the COPY statement."""
    out_dir = tmp_path / "D'Souza" / "tableau"
    con = build_synthetic_warehouse()
    build_marts(con)
    paths = export_tableau(con, out_dir)
    con.close()
    assert all(p.exists() for p in paths)
