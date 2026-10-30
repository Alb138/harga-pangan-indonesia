"""`pangan` command line: run one pipeline step, or `all` of them in order."""

import argparse
import logging
from collections.abc import Callable

import duckdb

from pangan import extract
from pangan.config import RAW_DIR, REF_DIR, WAREHOUSE_PATH
from pangan.marts import build_marts
from pangan.quality import quality_report
from pangan.warehouse import build_warehouse

log = logging.getLogger(__name__)


def cmd_extract() -> None:
    extract.main()


def cmd_build() -> None:
    build_warehouse(RAW_DIR, REF_DIR, WAREHOUSE_PATH)
    log.info("warehouse written to %s", WAREHOUSE_PATH)


def cmd_marts() -> None:
    with duckdb.connect(str(WAREHOUSE_PATH)) as con:
        for name in build_marts(con):
            count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            log.info("%-24s %9d rows", name, count)


def cmd_export() -> None:
    from pangan.export import export_tableau

    with duckdb.connect(str(WAREHOUSE_PATH), read_only=True) as con:
        for path in export_tableau(con):
            log.info("wrote %s", path)


def cmd_quality() -> None:
    with duckdb.connect(str(WAREHOUSE_PATH), read_only=True) as con:
        report = quality_report(con)
    coverage = report.pop("coverage")
    for key, value in report.items():
        print(f"{key:>15}: {value:,}")
    low = coverage[coverage["pct_business_days"] < 0.8]
    print(f"\nprovince-years below 80% business-day coverage: {len(low)} of {len(coverage)}")
    if not low.empty:
        print(low.to_string(index=False))


COMMANDS: dict[str, Callable[[], None]] = {
    "extract": cmd_extract,
    "build": cmd_build,
    "marts": cmd_marts,
    "export": cmd_export,
    "quality": cmd_quality,
}
PIPELINE = ["extract", "build", "marts", "export"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pangan", description=__doc__)
    parser.add_argument("command", choices=[*COMMANDS, "all"])
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    for step in PIPELINE if args.command == "all" else [args.command]:
        COMMANDS[step]()
    return 0
