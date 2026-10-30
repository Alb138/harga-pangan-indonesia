"""PihpsClient behaviour, exercised with a fake HTTP session (no network)."""

from datetime import date

import pytest
import requests

from pangan.pihps_client import PihpsClient

NOT_JSON = object()  # stands for an empty or HTML body served with status 200


class FakeResponse:
    def __init__(self, status_code: int, payload: object = None):
        self.status_code = status_code
        self._payload = {} if payload is None else payload

    def json(self) -> object:
        if self._payload is NOT_JSON:
            raise requests.JSONDecodeError("Expecting value", "", 0)
        return self._payload


class FakeSession:
    """Returns the queued responses in order and records every call."""

    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


def make_client(session: FakeSession) -> PihpsClient:
    return PihpsClient(session=session, delay_s=0, sleep=lambda s: None)


def test_retries_then_succeeds():
    ok = {"data": [{"id": 1, "name": "Aceh"}]}
    session = FakeSession([FakeResponse(500), FakeResponse(500), FakeResponse(200, ok)])
    assert make_client(session).get_provinces() == ok["data"]
    assert len(session.calls) == 3


def test_raises_after_max_retries():
    session = FakeSession([FakeResponse(500)])
    client = make_client(session)
    with pytest.raises(requests.HTTPError):
        client.get_provinces()
    assert len(session.calls) == client.max_retries + 1


def test_4xx_not_retried():
    session = FakeSession([FakeResponse(404)])
    with pytest.raises(requests.HTTPError):
        make_client(session).get_provinces()
    assert len(session.calls) == 1


def test_national_sends_empty_province():
    session = FakeSession([FakeResponse(200, {"data": []})])
    make_client(session).get_price_grid(1, None, date(2024, 3, 1), date(2024, 3, 8))
    params = session.calls[0]["params"]
    assert params["province_id"] == ""
    assert params["comcat_id"] == ",".join(f"cat_{i}" for i in range(1, 11))
    assert params["tipe_laporan"] == 1
    assert params["start_date"] == "2024-03-01"
    assert params["end_date"] == "2024-03-08"
    assert session.calls[0]["url"].endswith("/GetGridDataDaerah")


def test_retries_when_200_body_is_not_json():
    ok = {"data": []}
    session = FakeSession([FakeResponse(200, NOT_JSON), FakeResponse(200, ok)])
    assert make_client(session).get_price_grid(1, 10, date(2020, 1, 1), date(2020, 12, 31)) == ok
    assert len(session.calls) == 2


def test_retries_when_json_has_no_data_key():
    ok = {"data": []}
    session = FakeSession([FakeResponse(200, {"message": "error"}), FakeResponse(200, ok)])
    assert make_client(session).get_price_grid(1, 10, date(2020, 1, 1), date(2020, 12, 31)) == ok
    assert len(session.calls) == 2


def test_gives_up_on_persistent_bad_body():
    session = FakeSession([FakeResponse(200, NOT_JSON)])
    client = make_client(session)
    with pytest.raises(ValueError):
        client.get_provinces()
    assert len(session.calls) == client.max_retries + 1
