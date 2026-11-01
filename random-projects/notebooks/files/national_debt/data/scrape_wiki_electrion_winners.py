"""
Fetch US presidential election winners and their parties from Wikipedia.

Source table: "List of United States presidential elections by popular vote margin"
(covers every election 1788-2024). Only the Electoral College winner and party are kept.

Requirements:  pip install pandas requests lxml
Usage:         python fetch_election_winners.py
Output:        us_presidential_winners_wiki.json
"""

import re
import sys
from io import StringIO

import pandas as pd
import requests

URL = ("https://en.wikipedia.org/wiki/"
        "List_of_United_States_presidential_elections_by_popular_vote_margin")

# Wikipedia rejects requests without a descriptive User-Agent (HTTP 403).
# Put your own contact info here; that is Wikimedia's stated policy.
HEADERS = {"User-Agent": "election-winners-script/1.0 (personal project; contact: niro3177@colorado.edu)"}

# The table has a two-row header; columns are renamed by position.
# All 12 names are needed to parse the layout; only year/winner/party are kept.
# If Wikipedia editors add/remove a column, the length check below fails loudly
# instead of silently mislabeling data.
COLUMNS = [
    "record_year", "winner", "party_abbr",
    "ec_votes", "ec_pct",
    "pop_pct", "pop_margin_pct", "pop_votes", "pop_margin_votes",
    "runner_up", "runner_up_party_abbr",
    "turnout",
]

PARTY_NAMES = {
    "Ind.": "Independent",          # Washington; No party (going to drop him in the analysis anyway)
    "Fed.": "Federalist",
    "D-R": "Democratic-Republican",
    "NR": "National Republican",
    "Dem.": "Democratic",
    "Whig": "Whig",
    "Rep.": "Republican",
    "Prog.": "Progressive",
}

def fetch_html(url: str = URL):
    """
    Fetch the HTML of the Wikipedia page containing the election winners table.
    Parameters:
    -----------
    url (str): The URL of the Wikipedia page to fetch. Defaults to the election winners page.

    Returns:
    --------
    str: The HTML content of the page.
    """
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def strip_footnotes(s):
    """
    Remove footnote markers like [a] or [12] and stray whitespace.
    Parameters:
    -----------
    s (str): The string from which to remove footnotes.

    Returns:
    --------
    str: The string with footnotes removed.
    """
    if pd.isna(s):
        return s
    return re.sub(r"\[[^\]]*\]", "", str(s)).strip()


def parse(html: str):
    """
    Parse the HTML of the Wikipedia page to extract the election winners table.
    Parameters:
    -----------
    html (str): The HTML content of the Wikipedia page.

    Returns:
    --------
    pd.DataFrame: A DataFrame containing the parsed election winners data.
    """
    # match= picks the results table; read_html fills rowspans (e.g. a winner
    # name spanning two re-election rows) into every row automatically.
    tables = pd.read_html(StringIO(html), match="Runner-up")
    if len(tables) != 1:
        raise ValueError(f"Expected 1 matching table, found {len(tables)}")
    df = tables[0]

    if df.shape[1] != len(COLUMNS):
        raise ValueError(
            f"Table has {df.shape[1]} columns, expected {len(COLUMNS)}. "
            f"Wikipedia layout changed; inspect df.columns:\n{list(df.columns)}"
        )
    df.columns = COLUMNS
    df = df.apply(lambda col: col.map(strip_footnotes))

    # Drop any repeated header/footer rows: keep rows whose year starts with 4 digits.
    df = df[df["record_year"].astype(str).str.match(r"^\d{4}")].copy()
    df["record_year"] = df["record_year"].str[:4].astype(int)   # '1788–89' -> 1788

    df["party"] = df["party_abbr"].map(PARTY_NAMES)

    # The "Winner" column is the Electoral College winner (incl. House-decided
    # 1800/1824). Popular-vote and runner-up columns are only needed to parse
    # the table layout and are dropped here.
    return df[["record_year", "winner", "party", "party_abbr"]].reset_index(drop=True)


def validate(df: pd.DataFrame):
    """
    Validate the parsed election winners data.

    Parameters:
    -----------
    df (pd.DataFrame): The DataFrame to validate.

    Raises:
    -------
    ValueError: If the DataFrame fails validation.
    """
    # Check for any validation issues
    problems = []
    unmapped = sorted(set(df.loc[df["party"].isna(), "party_abbr"]))
    if unmapped:
        problems.append(f"Unmapped party abbreviations (add to PARTY_NAMES): {unmapped}")
    if df["record_year"].duplicated().any():
        problems.append(f"Duplicate years: {df.loc[df['record_year'].duplicated(), 'record_year'].tolist()}")
    expected = [1788] + list(range(1792, df["record_year"].max() + 1, 4))
    missing = sorted(set(expected) - set(df["record_year"]))
    if missing:
        problems.append(f"Missing election years: {missing}")
    if df["winner"].isna().any():
        problems.append(f"Missing winner names in years: {df.loc[df['winner'].isna(), 'record_year'].tolist()}")
    if problems:
        raise ValueError("Validation failed:\n  " + "\n  ".join(problems))


# Mid-term changes in the president's PARTY. Deaths/resignations where the
# successor shared the party (e.g. Coolidge, Truman, LBJ, Ford) need no entry.
# These are judgment calls; edit them to match your coding scheme.
MIDTERM_PARTY_CHANGES = [
    # Tyler took over as a Whig (Apr 4, 1841) but was expelled from the party.
    ("1841-09-13", "Unaffiliated"),
    # Lincoln assassinated; Andrew Johnson was a Democrat elected on the
    # National Union ticket. Use "Democratic" instead if that suits your analysis.
    ("1865-04-15", "National Union"),
]


def inauguration_date(election_year: int):
    """
    Date the winner of a given election took office.
    
    Parameters:
    -----------
    election_year (int): The year of the presidential election.

    Returns:
    --------
    pd.Timestamp: The date the winner took office.
    """
    if election_year == 1788:
        return pd.Timestamp("1789-04-30")
    if election_year <= 1932:                  # 20th Amendment moved it to Jan 20
        return pd.Timestamp(f"{election_year + 1}-03-04")
    return pd.Timestamp(f"{election_year + 1}-01-20")


def party_by_year(elections: pd.DataFrame, end=None) -> pd.DataFrame:
    """
    One row per calendar year 1789..end with the party in the White House.

    Parameters:
    -----------
    elections (pd.DataFrame): DataFrame containing election winners and their parties.
    end (str or pd.Timestamp, optional): The last year to include. Defaults to today.

    Returns:
    --------
    pd.DataFrame: DataFrame with columns 'record_date' (Jan 1 of the year) and 'party',
    indicating the party that held the presidency for the most days of that year.

    Rule: the party that held the presidency for the MOST DAYS of that year.
    (Election years are mostly held by the outgoing party, since inauguration
    came in March/January of the following year.)
    """
    end = pd.Timestamp(end) if end is not None else pd.Timestamp.today().normalize()

    # A missing party (e.g. Washington coded as NaN) would make groupby drop
    # those years silently, so label it explicitly.
    parties = elections["party"].fillna("No party")
    events = [(inauguration_date(y), p) for y, p in zip(elections["record_year"], parties)]
    events += [(pd.Timestamp(d), p) for d, p in MIDTERM_PARTY_CHANGES]
    timeline = (pd.DataFrame(events, columns=["start", "party"])
                  .sort_values("start").set_index("start")["party"])

    days = pd.date_range("1789-04-30", end, freq="D")
    daily = timeline.reindex(timeline.index.union(days)).ffill().loc[days]

    counts = daily.groupby([daily.index.year, daily.values]).size()
    counts.index.names = ["record_year", "party"]
    result = (counts.reset_index(name="days")
                    .sort_values(["record_year", "days"], ascending=[True, False])
                    .drop_duplicates("record_year")[["record_year", "party"]]
                    .reset_index(drop=True))
    # One row per year, keyed by Jan 1 so it joins against the daily debt series.
    result["record_date"] = result["record_year"].astype(str) + "-01-01"
    return result[["record_date", "party"]]


def wiki_parse():
    df = parse(fetch_html())
    validate(df)
    out = df[["record_year", "winner", "party"]]
    out.to_json("us_presidential_winners_wiki.json", orient="records", indent=2)
    print(f"Saved {len(out)} elections ({out['record_year'].min()}-{out['record_year'].max()}) "
          "to us_presidential_winners_wiki.json")

    years = party_by_year(out)
    years.to_json("us_party_in_power_by_year.json", orient="records", indent=2)
    print(f"Saved {len(years)} years ({years['record_date'].min()}-{years['record_date'].max()}) "
          "to us_party_in_power_by_year.json")
    print(years["party"].value_counts().to_string())
    return years


if __name__ == "__main__":
    try:
        wiki_parse()
    except Exception as e:
        sys.exit(f"ERROR: {e}")