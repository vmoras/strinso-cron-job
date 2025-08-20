# main.py
import os
import sys
import json
import datetime as dt
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def parse_time_from_response(resp: requests.Response) -> Optional[str]:
    """
    Tries common time APIs:
      - worldtimeapi.org → JSON key 'utc_datetime'
      - timeapi.io → JSON key 'dateTime' (ISO8601 UTC)
    Falls back to HTTP 'Date' header if JSON not recognized.
    """
    try:
        data = resp.json()
        # worldtimeapi.org sample: {"utc_datetime":"2025-08-20T12:34:56.789Z", ...}
        if isinstance(data, dict) and "utc_datetime" in data:
            return data["utc_datetime"]
        # timeapi.io sample: {"dateTime":"2025-08-20T12:34:56.789Z", ...}
        if isinstance(data, dict) and "dateTime" in data:
            return data["dateTime"]
    except json.JSONDecodeError:
        pass

    # Fallback: RFC 1123 'Date' header in UTC; convert to ISO 8601
    hdr = resp.headers.get("Date")
    if hdr:
        try:
            # Example: 'Wed, 20 Aug 2025 12:34:56 GMT'
            dt_utc = dt.datetime.strptime(hdr, "%a, %d %b %Y %H:%M:%S %Z")
            return dt_utc.replace(tzinfo=dt.timezone.utc).isoformat()
        except Exception:
            return None
    return None


def main():
    url = os.getenv(
        "TIME_URL",
        # default to a reliable free endpoint that returns UTC time in JSON
        "https://worldtimeapi.org/api/timezone/Etc/UTC",
    )
    timeout = float(os.getenv("HTTP_TIMEOUT", "10"))

    session = get_session()
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        utc_iso = parse_time_from_response(resp)
        if not utc_iso:
            print(f"[WARN] Could not parse UTC from response. Status={resp.status_code}")
            print(resp.text[:500])
            sys.exit(2)

        print(f"[OK] Current UTC time: {utc_iso}")
        sys.exit(0)
    except requests.RequestException as e:
        print(f"[ERROR] HTTP error calling {url}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
