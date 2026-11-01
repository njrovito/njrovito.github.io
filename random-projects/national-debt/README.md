# national_debt

US national debt over time, overlaid with which party held the presidency.

## Website

`index.html` is a self-contained static page (no build step) that reads the
JSON data in `data/` directly in the browser with Chart.js and renders:

- Total debt over time
- The derivative of debt with respect to time (billions/year)

Both charts are shaded by the party in power, with a "years of history"
control to adjust the window.


### Run locally

Browsers block `fetch()` against `file://` URLs, so serve the folder instead
of opening `index.html` directly:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Data pipeline (Python)

- `data/scrape_wiki_electrion_winners.py` scrapes presidential election
  winners from Wikipedia and writes `data/us_presidential_winners_wiki.json`
  and `data/us_party_in_power_by_year.json`.
- `data/hst_debt.json` is historical U.S. Treasury debt data.
- `main.py` / `debt_viz.py` reproduce the same two charts as static
  matplotlib figures (`debt_and_derivative_with_party_background.png`) for
  use outside the browser.
