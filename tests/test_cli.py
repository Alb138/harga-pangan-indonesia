"""The `pangan` command dispatches to the right pipeline step(s)."""

import pytest

from pangan import cli


@pytest.fixture
def calls(monkeypatch) -> list[str]:
    called: list[str] = []
    for name in cli.COMMANDS:
        monkeypatch.setitem(cli.COMMANDS, name, lambda name=name: called.append(name))
    return called


def test_cli_dispatch(calls):
    assert cli.main(["build"]) == 0
    assert calls == ["build"]


def test_cli_quality(calls):
    cli.main(["quality"])
    assert calls == ["quality"]


def test_cli_all_runs_pipeline_in_order(calls):
    assert cli.main(["all"]) == 0
    assert calls == ["extract", "build", "marts", "export"]


def test_cli_rejects_unknown_command(calls):
    with pytest.raises(SystemExit):
        cli.main(["deploy"])
    assert calls == []
