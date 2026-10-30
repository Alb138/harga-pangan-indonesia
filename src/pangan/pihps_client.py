"""Small, polite client for the JSON endpoints behind Bank Indonesia's PIHPS price table."""

import time
from collections.abc import Callable
from datetime import date

import requests

from pangan.config import (
    BASE_URL,
    CATEGORY_IDS,
    MAX_RETRIES,
    REQUEST_DELAY_S,
    TIMEOUT_S,
    USER_AGENT,
)

HEADERS = {"User-Agent": USER_AGENT, "X-Requested-With": "XMLHttpRequest"}


class PihpsClient:
    """Sequential requests with a pause between them, retrying only transient failures."""

    def __init__(
        self,
        session: requests.Session | None = None,
        delay_s: float = REQUEST_DELAY_S,
        timeout_s: float = TIMEOUT_S,
        max_retries: int = MAX_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.session = session or requests.Session()
        self.delay_s = delay_s
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.sleep = sleep
        self._has_requested = False

    def get_provinces(self) -> list[dict]:
        return self._get("GetRefProvince")["data"]

    def get_commodities(self) -> list[dict]:
        return self._get("GetRefCommodityAndCategory")["data"]

    def get_price_grid(
        self, price_type_id: int, province_id: int | None, start: date, end: date
    ) -> dict:
        """Daily prices for every commodity; `province_id=None` asks for the national series."""
        params = {
            "price_type_id": price_type_id,
            "comcat_id": ",".join(CATEGORY_IDS),
            "province_id": "" if province_id is None else province_id,
            "regency_id": "",
            "market_id": "",
            "tipe_laporan": 1,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        return self._get("GetGridDataDaerah", params)

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{BASE_URL}/{endpoint}"
        for attempt in range(self.max_retries + 1):
            if self._has_requested:
                self.sleep(self.delay_s)
            self._has_requested = True
            try:
                response = self.session.get(
                    url, params=params, headers=HEADERS, timeout=self.timeout_s
                )
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.max_retries:
                    raise
            else:
                if response.status_code >= 400:
                    error = requests.HTTPError(f"{response.status_code} from {url}")
                    if response.status_code < 500 or attempt == self.max_retries:
                        raise error
                else:
                    payload = _data_payload(response)
                    if payload is not None:
                        return payload
                    if attempt == self.max_retries:
                        raise ValueError(f"no usable JSON from {url} after {attempt + 1} tries")
            self.sleep(5 * 2**attempt)
        raise AssertionError("unreachable")


def _data_payload(response: requests.Response) -> dict | None:
    """The server sometimes answers 200 with an empty or non-JSON body; treat that as transient."""
    try:
        payload = response.json()
    except requests.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) and "data" in payload else None
