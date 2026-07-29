# Portfolio Analysis Dashboard

A self-contained household net-worth dashboard. All financial data lives
**encrypted inside this repository** (`data.enc.json`) — no Google Sheets, no
third-party services. Prices refresh automatically via GitHub Actions, and
edits are made in the dashboard's built-in editor, which commits changes back
to the repo through the GitHub API.

## How it works

| Piece | What it does |
| --- | --- |
| `index.html` | The entire dashboard: full-lock passphrase screen, analytics, and the data editor |
| `data.enc.json` | All holdings/properties/profile data, AES-256-GCM encrypted in your browser |
| `tickers.json` | Plain list of ticker symbols (only thing readable without the passphrase) |
| `prices.json` | Latest ASX prices + AUD/INR, written by the scheduled workflow |
| `.github/workflows/prices.yml` | Fetches prices ~4× per ASX trading day (and on demand) |
| `scripts/fetch_prices.py` | The fetcher — Yahoo Finance quotes with a frankfurter.app FX fallback |

## First-time setup

1. Open the dashboard (GitHub Pages URL). You'll get a **setup wizard**:
   - *Import from my Google Sheet* (one-time; link-sharing can be turned off
     right after) or *Start fresh*.
   - Choose a **passphrase** (min 8 chars). This encrypts everything and is
     required to view the dashboard. **It cannot be reset** — export a backup
     from the editor and keep it somewhere safe.
   - Create a **fine-grained GitHub token** (the wizard links to the right
     page): Repository access = only this repo; Permissions = *Contents: Read
     and write* (plus *Actions: Read and write* if you want new tickers priced
     immediately). Paste it in — it stays in your browser only.
2. That's it. On any other device: open the URL, enter the passphrase
   (and paste the token there too if you want to edit from that device).

## Day-to-day use

- **View**: open the page, enter your passphrase (or tick *Keep me unlocked on
  this device*). Prices auto-refresh every 5 minutes while the tab is open.
- **Bought shares?** ✎ Edit → press **＋** on the holding → enter the **new
  total shares** and **what you paid for the top-up** — shares bought and the
  cost-basis increase are computed for you. (A lower total records a sale,
  reducing the cost basis proportionally.)
- **New holding/property, changed offset?** ✎ Edit → change the field or add a
  row → **Save to GitHub**. Every save is a commit, so the repo history is a
  complete audit trail of your data (encrypted at every point).
- **Lock** button clears the keys from the device immediately.

## Security model

- The passphrase derives an AES-256-GCM key in the browser (PBKDF2,
  310k iterations). Data is encrypted/decrypted **only in the browser**; the
  passphrase and key never leave it. The public Pages site exposes only
  ciphertext, the ticker list, and prices.
- The GitHub token is stored in the browser's localStorage and sent only to
  `api.github.com`. Scope it to this single repository.
- Anyone without the passphrase sees a lock screen — even with the URL.
- **There is no passphrase recovery.** Use ✎ Edit → *Export data backup* after
  meaningful changes and keep the file safe. Restoring = setup wizard → import
  backup (or Edit → Import data backup).
- Historic note: git history from the Google-Sheets era contains the old
  spreadsheet's file ID. Once you've imported, set that sheet's sharing to
  **Restricted** (Share → General access) and it's inert.

## The price feed

`prices.yml` runs on a schedule during ASX hours and can be run manually
(Actions tab → *Update prices* → *Run workflow*). It reads `tickers.json`,
fetches each ticker with an `.AX` suffix from Yahoo Finance, gets AUD/INR, and
commits `prices.json` only when something changed. If a ticker has no price
yet (brand-new purchase), the dashboard flags it and uses the fallback price
you set in the editor until the next run.

> GitHub pauses scheduled workflows on repos with no activity for ~60 days.
> The dashboard warns you when prices look stale; one click of *Run workflow*
> in the Actions tab revives it.

## Net-worth conventions

- Property **net equity = value − loan + offset** — offset cash cancels the
  loan dollar-for-dollar, so a fully offset loan counts as 100% ownership.
- Net worth = equities market value + property net equity (super excluded).

## The wealth-history chart

The chart is **reconstructed, not recorded**: the price workflow publishes a
year of real daily closes per ticker (`history.json`), and the dashboard
multiplies them by the holdings you had on each date. Every editor save
stores a snapshot (date, property equity, share counts) inside the encrypted
data file, so purchases, sales and property revaluations step in on the right
dates; dates before your first save assume the oldest recorded mix. This
means the chart is identical on every device, needs no browser storage, and
extends back a full year from day one.

Views: **Stacked** (property equity + equities; the top edge is net worth),
or single lines for **Net worth / Equities / Property**, over **3M / 6M / 1Y /
All**.
