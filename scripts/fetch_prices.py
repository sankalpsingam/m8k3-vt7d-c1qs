#!/usr/bin/env python3
"""Fetch ASX prices + AUD/INR for the dashboard's price feed.

Reads the ticker list from tickers.json (maintained by the dashboard's
editor), fetches quotes from Yahoo Finance (tickers get an .AX suffix),
and writes prices.json. The AUD/INR rate falls back to frankfurter.app
(ECB reference rates) if Yahoo is unavailable.

Only writes prices.json when a price or the FX rate actually changed, so
scheduled runs don't create empty commits. Stdlib only — no dependencies.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}


def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def yahoo_price(symbol):
    data = get_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
    )
    price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    return round(float(price), 4)


def main():
    tickers = []
    if os.path.exists("tickers.json"):
        try:
            tickers = json.load(open("tickers.json")).get("tickers", [])
        except Exception as exc:
            print(f"warn: could not read tickers.json: {exc}")

    prev = {}
    if os.path.exists("prices.json"):
        try:
            prev = json.load(open("prices.json"))
        except Exception:
            prev = {}
    prev_prices = prev.get("prices", {})

    # keep only currently-held tickers so stale symbols age out of the feed
    prices = {}
    failures = []
    for t in tickers:
        try:
            prices[t] = yahoo_price(f"{t}.AX")
        except Exception as exc:
            failures.append(t)
            if t in prev_prices:  # keep the last known price on a bad fetch
                prices[t] = prev_prices[t]
            print(f"warn: {t}: {exc}")

    fx = prev.get("fx", {}).get("AUDINR")
    try:
        fx = yahoo_price("AUDINR=X")
    except Exception as exc:
        print(f"warn: Yahoo FX failed ({exc}), trying frankfurter.app")
        try:
            data = get_json("https://api.frankfurter.app/latest?from=AUD&to=INR")
            fx = round(float(data["rates"]["INR"]), 4)
        except Exception as exc2:
            print(f"warn: frankfurter FX failed too: {exc2}")

    if not tickers and fx is None:
        print("Nothing to do (no tickers, no FX).")
        return

    unchanged = (
        prices == prev_prices
        and fx == prev.get("fx", {}).get("AUDINR")
    )
    if unchanged:
        print("No changes — leaving prices.json untouched.")
        return

    out = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fx": {"AUDINR": fx},
        "prices": dict(sorted(prices.items())),
    }
    with open("prices.json", "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(f"Wrote prices.json: {len(prices)} tickers, FX={fx}, failures={failures}")


if __name__ == "__main__":
    sys.exit(main())
