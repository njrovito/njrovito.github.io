# national_debt

US national debt over time, overlaid with which party held the presidency.

## Website

`index.html` is a static page (no build step). It loads `debt_viz.py` and the
JSON in `data/` into Pyodide (Python in the browser), which does all the data
processing; Chart.js draws the result. It renders:

- Total debt over time
- The derivative of debt with respect to time (billions/year)

Both charts are shaded by the party in power, with From/To year inputs to
pick the date range. The first load downloads Pyodide, numpy, and pandas, so
it takes a few seconds.


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
- `debt_viz.py` is the single source of truth for the data processing (used by
  the page through Pyodide). Run it directly to produce the same two charts as
  a static matplotlib figure (`debt_and_derivative_with_party_background.png`),
  with optional `--start` / `--end`.
