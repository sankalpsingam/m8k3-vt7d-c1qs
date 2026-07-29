#!/usr/bin/env python3
"""Fetch ASX prices + AUD/INR + daily price history for the dashboard.

Reads the ticker list from tickers.json (maintained by the dashboard's
editor), fetches quotes from Yahoo Finance (tickers get an .AX suffix),
and writes:
  - prices.json   — latest price per ticker + AUD/INR
  - history.json  — one year of daily closes per ticker, from which the
                    dashboard reconstructs the wealth-history chart

The AUD/INR rate falls back to frankfurter.app (ECB reference rates) if
Yahoo is unavailable. Files are only written when their content actually
changed, so scheduled runs don't create empty commits. Stdlib only.
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


def yahoo_history(symbol, range_="1y"):
    """Daily closes as [[YYYY-MM-DD, close], ...] (UTC dates, nulls skipped)."""
    data = get_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_}&interval=1d"
    )
    result = data["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    closes = (result.get("indicators", {}).get("quote", [{}])[0].get("close")) or []
    out = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
        out.append([day, round(float(close), 4)])
    return out


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
    else:
        out = {
            "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fx": {"AUDINR": fx},
            "prices": dict(sorted(prices.items())),
        }
        with open("prices.json", "w") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
        print(f"Wrote prices.json: {len(prices)} tickers, FX={fx}, failures={failures}")

    # ---- Daily close history for the wealth chart ----
    prev_hist = {}
    if os.path.exists("history.json"):
        try:
            prev_hist = json.load(open("history.json"))
        except Exception:
            prev_hist = {}
    prev_series = prev_hist.get("series", {})

    series = {}
    for t in tickers:
        try:
            series[t] = yahoo_history(f"{t}.AX")
        except Exception as exc:
            if t in prev_series:  # keep last known history on a bad fetch
                series[t] = prev_series[t]
            print(f"warn: history {t}: {exc}")

    if series and series != prev_series:
        hist_out = {
            "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "series": dict(sorted(series.items())),
        }
        with open("history.json", "w") as f:
            json.dump(hist_out, f, separators=(",", ":"))
            f.write("\n")
        days = max((len(v) for v in series.values()), default=0)
        print(f"Wrote history.json: {len(series)} tickers, ~{days} trading days")
    else:
        print("No history changes.")


if __name__ == "__main__":
    sys.exit(main())
