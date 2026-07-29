# Portfolio Analysis Dashboard

A single-file (`index.html`), zero-build household net-worth dashboard. It reads a
Google Sheet as CSV and renders holdings, real estate, allocation, concentration
analytics, a FIRE-goal projection and rule-based portfolio signals. No server, no
framework — open the file (or host it on GitHub Pages) and go.

## Setup

1. Open `index.html` in a browser (or your hosted copy).
2. You'll see a **Connect your data source** screen. Paste either:
   - **Your Google Sheet tab URL** — copy it from the address bar so it includes
     `gid=…`. The sheet must have link-sharing on
     (Share → General access → *Anyone with the link* → *Viewer*), **or**
   - **An Apps Script proxy URL** (recommended — keeps the sheet private, see below).
3. Done. The URL is stored only in that browser's `localStorage` — it is never
   committed to this repository. Use the ⚙ button to change it later.

## Privacy

Earlier versions hardcoded the spreadsheet's file ID in `index.html`, which meant
anyone with access to this repo (or the page source) could download the sheet.
That is no longer the case — the source contains no sheet ID, no names, no
property addresses. Two things to be aware of:

- **Git history still contains the old file ID.** If this repo is (or ever
  becomes) visible to others, either restrict the sheet's sharing (best — see
  the proxy below) or copy your data into a fresh spreadsheet so the old ID is
  dead, then turn off sharing on the old one.
- **Direct CSV access requires "Anyone with the link" sharing.** Anyone who
  obtains the URL can read the sheet. The Apps Script proxy removes this
  requirement entirely.

### Keeping the sheet fully private (Apps Script proxy)

`apps-script/Code.gs` is a ~40-line Google Apps Script that reads the sheet with
*your* credentials and serves CSV only to callers presenting a shared-secret
token. Setup takes about two minutes — instructions are in the file's header
comment. Once deployed, paste the `…/exec?token=…` URL into the dashboard's ⚙
settings and set the spreadsheet back to **Restricted**.

## Expected sheet layout

The dashboard detects rows by shape, not position, so you can add owners,
holdings or properties freely:

- **Holdings rows** — an owner name, an ASX-style ticker (e.g. `VGS`), shares,
  price, market value, cost basis and gain %. If a header row containing
  `Ticker` exists, columns are mapped by name (`Shares`, `Price`,
  `Market Value`, `Cost Basis`, `Gain %`, optional `Sector`); otherwise the
  original column positions are assumed. A blank owner cell inherits the owner
  above it.
- **Property rows** — a name plus CMA low / estimate / high, loan, offset,
  updated, source. Names containing `PPOR` are tagged as owner-occupied. Rows
  whose name contains `Total`/`Subtotal`/`Combined`/`Sum` are ignored.
  **Net equity is computed by the dashboard as `value − loan + offset`** —
  offset cash cancels the loan dollar-for-dollar, so a fully offset loan
  counts as 100% ownership. The sheet's own Net Equity column, if present, is
  not used for the maths.
- **Profile rows** — simple `Label, Value` pairs (e.g. `Risk Tolerance`,
  `Monthly Savings Rate`, the FIRE assumption fields, `AUD/INR Exchange Rate
  (Live)`).

## Features

- **Live data** with a 5-minute auto-refresh (paused while the tab is hidden).
  A failed refresh keeps the last good data on screen with a warning banner
  instead of wiping the dashboard.
- **Concentration analytics** — largest position, HHI, top sector exposure and
  largest single asset, all aggregated per-ticker across owners.
- **Rule-based signals** — oversized positions (diversified ETFs exempt),
  sector concentration, large-loss verification / tax-loss harvesting
  candidates, duplicated holdings across owners, savings automation and
  FX-mismatch prompts. All generated from live data by fixed thresholds;
  informational only, not financial advice.
- **FIRE projection** — inflates the INR-denominated target each year while
  compounding the portfolio, and reports the crossover year.
- **Net-worth history** — one snapshot per local calendar day in
  `localStorage`, charted with an equities overlay. History is per-browser;
  use the Export/Import buttons on the chart card to move it between devices.
- **Light/dark theme**, mobile-friendly layout, keyboard-accessible controls.
