"""Job planning and the resumable, crash-safe extract loop."""

import json
from datetime import date

import pytest

from pangan.extract import Job, build_jobs, run_extract


class FakeClient:
    def __init__(self, fail_on_call: int | None = None):
        self.grid_calls: list[tuple] = []
        self.fail_on_call = fail_on_call

    def get_provinces(self) -> list[dict]:
        return [{"id": 1, "name": "Aceh"}]

    def get_commodities(self) -> list[dict]:
        return [{"id": "com_1", "name": "Beras Kualitas Bawah I", "cat_id": "cat_1"}]

    def get_price_grid(self, price_type_id, province_id, start, end) -> dict:
        self.grid_calls.append((price_type_id, province_id, start, end))
        if self.fail_on_call == len(self.grid_calls):
            raise RuntimeError("server went away")
        return {"data": [{"no": 1, "name": "Beras Kualitas Bawah I", "level": 2}]}


def test_build_jobs_count():
    jobs = build_jobs([1, 13], range(2018, 2020))
    province_jobs = [j for j in jobs if j.province_id is not None]
    national_jobs = [j for j in jobs if j.province_id is None]
    assert len(jobs) == 12
    assert {j.price_type_id for j in province_jobs} == {1}
    assert len(province_jobs) == 4
    assert {j.price_type_id for j in national_jobs} == {1, 2, 3, 4}


def test_first_year_starts_on_start_date():
    assert Job(1, 13, 2018).date_range() == (date(2018, 1, 1), date(2018, 12, 31))


def test_last_year_clipped():
    assert Job(1, 13, 2026).date_range() == (date(2026, 1, 1), date(2026, 9, 30))


def test_cache_path_layout(tmp_path):
    assert Job(1, 13, 2024).cache_path(tmp_path) == tmp_path / "pt1/prov13/2024.json"
    assert Job(3, None, 2024).cache_path(tmp_path) == tmp_path / "pt3/provnational/2024.json"


def test_resume_skips_cached(tmp_path):
    jobs = [Job(1, 1, 2018), Job(1, 1, 2019), Job(2, None, 2018)]
    cached = jobs[0].cache_path(tmp_path)
    cached.parent.mkdir(parents=True)
    cached.write_text('{"data": []}', encoding="utf-8")

    client = FakeClient()
    fetched = run_extract(client, jobs, tmp_path)

    assert fetched == 2
    assert [(c[0], c[1]) for c in client.grid_calls] == [(1, 1), (2, None)]
    assert json.loads(jobs[1].cache_path(tmp_path).read_text(encoding="utf-8"))["data"]
    assert (tmp_path / "ref_provinces.json").exists()
    assert (tmp_path / "ref_commodities.json").exists()


def test_no_partial_file_on_failure(tmp_path):
    jobs = [Job(1, 1, 2018), Job(1, 1, 2019)]
    with pytest.raises(RuntimeError):
        run_extract(FakeClient(fail_on_call=2), jobs, tmp_path)

    assert jobs[0].cache_path(tmp_path).exists()
    assert not jobs[1].cache_path(tmp_path).exists()
    assert list(tmp_path.rglob("*.tmp")) == []
