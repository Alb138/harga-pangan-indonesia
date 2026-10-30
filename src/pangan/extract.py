"""Plan the download jobs and run them with a crash-safe, resumable file cache."""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from pangan.config import END_DATE, RAW_DIR, REF_DIR, START_DATE
from pangan.pihps_client import PihpsClient

log = logging.getLogger(__name__)

TRADITIONAL_MARKET = 1
ALL_MARKET_TYPES = (1, 2, 3, 4)


@dataclass(frozen=True)
class Job:
    """One request: one market type, one province (None = national), one calendar year."""

    price_type_id: int
    province_id: int | None
    year: int

    def date_range(self) -> tuple[date, date]:
        return max(date(self.year, 1, 1), START_DATE), min(date(self.year, 12, 31), END_DATE)

    def cache_path(self, raw_dir: Path) -> Path:
        province = self.province_id if self.province_id is not None else "national"
        return raw_dir / f"pt{self.price_type_id}" / f"prov{province}" / f"{self.year}.json"


def build_jobs(province_ids: list[int], years: range) -> list[Job]:
    """Traditional-market prices per province, plus all four market types nationally."""
    jobs = [Job(TRADITIONAL_MARKET, pid, year) for pid in province_ids for year in years]
    jobs += [Job(pt, None, year) for pt in ALL_MARKET_TYPES for year in years]
    return jobs


def _write_json_atomic(path: Path, payload: object) -> None:
    """Write to a temp file and rename, so an interrupted run never leaves a half file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def run_extract(client: PihpsClient, jobs: list[Job], raw_dir: Path) -> int:
    """Fetch every job that is not cached yet; return how many were fetched."""
    for name, fetch in [
        ("ref_provinces.json", client.get_provinces),
        ("ref_commodities.json", client.get_commodities),
    ]:
        if not (raw_dir / name).exists():
            _write_json_atomic(raw_dir / name, fetch())

    todo = [job for job in jobs if not job.cache_path(raw_dir).exists()]
    log.info("%d jobs cached, %d to fetch", len(jobs) - len(todo), len(todo))
    started = time.monotonic()
    for done, job in enumerate(todo, start=1):
        start, end = job.date_range()
        payload = client.get_price_grid(job.price_type_id, job.province_id, start, end)
        _write_json_atomic(job.cache_path(raw_dir), payload)
        eta_min = (time.monotonic() - started) / done * (len(todo) - done) / 60
        log.info("[%d/%d] %s, ETA %.0f min", done, len(todo), job, eta_min)
    return len(todo)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    province_ids = pd.read_csv(REF_DIR / "provinces.csv")["pihps_id"].tolist()
    jobs = build_jobs(province_ids, range(START_DATE.year, END_DATE.year + 1))
    fetched = run_extract(PihpsClient(), jobs, RAW_DIR)
    log.info("%d jobs fetched", fetched)
    return 0
