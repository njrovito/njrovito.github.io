import numpy as np 
import matplotlib.pyplot as plt
from matplotlib import rcParams

import pandas as pd

# Set global font sizes and weights for plots
rcParams.update({
    'axes.titlesize': 16,
    'axes.labelsize': 12,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'font.weight': 'bold',
    'axes.titleweight': 'bold',
    'axes.labelweight': 'bold',
})

# Constants 
DEBT_JSON_PATH = 'data/hst_debt.json'
PARTY_JSON_PATH = 'data/us_party_in_power_by_year.json'

DEM_COLOR = '#0015BC'
REP_COLOR = '#E9141D'
DEM_REP_COLOR = '#6E6E6E'  # Gray color for Democratic-Republican party
FED_COLOR = "#16E220"  # Gold color for Federalist party
WHIG_COLOR = "#F7941D"  # Orange color for Whig party
UNAFFILIATED_COLOR = "#000000"  # Black color for Unaffiliated
NATIONAL_UNION_COLOR = "#8B4513"  # Brown color for National Union party
INDEPENDENT_COLOR = "#A9A9A9"  # Light gray color for Independent/no party

PARTY_COLORS_DICT = {
    'Democratic': DEM_COLOR,
    'Republican': REP_COLOR,
    'Democratic-Republican': DEM_REP_COLOR,
    'Federalist': FED_COLOR,
    'Whig': WHIG_COLOR,
    'Unaffiliated': UNAFFILIATED_COLOR,
    'National Union': NATIONAL_UNION_COLOR,
    'Independent': INDEPENDENT_COLOR,
    'No party': INDEPENDENT_COLOR,
}

def check_df_for_nan(df):
    """
    Checks for NaN values in the DataFrame and raises an error if any are found.

    Parameters:
    -----------
    df (pd.DataFrame): DataFrame to check for NaN values.

    Raises:
    -------
    ValueError: If any NaN values are found in the DataFrame.
    """

    # Look for NaN values in the DataFrame
    nan_values = df.isna().sum()

    if nan_values.any():
        raise ValueError(f"NaN values found in the debt data:\n{nan_values}")

def parse_party_json(party_json):
    """
    Parses the party JSON data and returns a DataFrame.

    Parameters:
    -----------
    party_json (str): Path to the JSON file containing party data.

    Returns:
    --------
    pd.DataFrame: DataFrame containing the parsed party data.
    """

    party_data = pd.read_json(party_json)

    print(party_data.head())
    
    party_data.sort_values(by='record_date', ascending=True, inplace=True)\
    
    return party_data

def parse_debt_json(debt_json):
    """
    Parses the debt JSON data and returns a DataFrame.
    
    Parameters:
    -----------
    debt_json (str): Path to the JSON file containing debt data.
    
    Returns:
    --------
    pd.DataFrame: DataFrame containing the parsed debt data.
    """
    
    debt_data = pd.read_json('data/hst_debt.json')


    normalized_data = pd.json_normalize(debt_data['data'])
    normalized_data.sort_values(by='record_date', ascending=True, inplace=True)
    normalized_data['debt_outstanding_amt'] = pd.to_numeric(normalized_data['debt_outstanding_amt'], errors='raise').astype(float)
    
    check_df_for_nan(normalized_data)

    return normalized_data

def restrict_n_yeats(df, n_years=100):
    """
    Restricts the DataFrame to the last n years of data, plus the years up to the last presidental year. 

    E.g., if the current year - n = presidental year, then the data will be restricted to the last n years. 
    If the current year - n = non-presidental year, then the data will be restricted to the last n years plus 
    the years up to the last presidental year.
    
    Parameters:
    -----------
    df (pd.DataFrame): DataFrame containing debt data.
    
    Returns:
    --------
    pd.DataFrame: DataFrame restricted to the last n years of data.
    """
    current_year = pd.Timestamp.now().year

    # Get the number of years offset from the last presidentional electrion 
    # Presidents get into office in the year after the election, 
    # so we need to subtract 1 from the offset to get the number of years in office.
    years_since_election = current_year % 4
    years_in_office = years_since_election - 1 
    coverage = n_years + years_in_office

    search_year = current_year - coverage

    hundred_years_ago = search_year - 1  # Subtract 1 to include the year of the last presidental election
    df['record_date'] = pd.to_datetime(df['record_date'])
    restricted_df = df[df['record_date'].dt.year >= hundred_years_ago]
    
    return restricted_df

def convert_to_billions(df):
    """
    Converts the debt outstanding amount to billions.

    Parameters:
    -----------
    df (pd.DataFrame): DataFrame containing debt data.

    Returns:
    --------
    pd.DataFrame: DataFrame with debt outstanding amount converted to billions.
    """

    df['debt_outstanding_amt'] = df['debt_outstanding_amt'] / 1e9
    return df

def add_debt_derivative(df):
    """
    Adds a column with the time derivative of the debt (d(debt)/dt), in units
    of debt_outstanding_amt per year.

    Records aren't evenly spaced (e.g. gaps around leap years), so the
    derivative is computed against the actual elapsed time between
    records rather than assuming a fixed step. np.gradient is used so
    endpoints get a one-sided difference instead of being dropped.

    Parameters:
    -----------
    df (pd.DataFrame): DataFrame with 'record_date' (datetime) and
    'debt_outstanding_amt' columns, sorted by record_date.

    Returns:
    --------
    pd.DataFrame: DataFrame with an added 'debt_derivative' column.
    """

    years_elapsed = (df['record_date'] - df['record_date'].iloc[0]).dt.days / 365.25
    df['debt_derivative'] = np.gradient(df['debt_outstanding_amt'], years_elapsed)
    return df

def main():
    df_debt = parse_debt_json(DEBT_JSON_PATH)
    df_prty = parse_party_json(PARTY_JSON_PATH)

    df_debt = restrict_n_yeats(df_debt, n_years=50)
    df_prty = restrict_n_yeats(df_prty, n_years=50)

    df_debt = convert_to_billions(df_debt)
    df_debt = add_debt_derivative(df_debt)


    # Assign party colors to the DataFrame based on the party in power

    print(df_prty.head())
    # Map the party colors to the DataFrame
    df_prty['party_color'] = df_prty['party'].map(PARTY_COLORS_DICT)
    unmapped_parties = df_prty.loc[df_prty['party_color'].isna(), 'party'].unique()
    if len(unmapped_parties):
        raise ValueError(f"No color defined for party/parties: {list(unmapped_parties)}")


    _, ax = plt.subplots(1, 2, figsize=(12, 6))

    # Plot total debt over time
    ax[0].plot(df_debt['record_date'], df_debt['debt_outstanding_amt'], label='Total Debt', color='black', linewidth=4)

    # Add background color for each party in power
    for _, row in df_prty.iterrows():
        start_date = row['record_date']
        end_date = start_date + pd.DateOffset(years=1)
        ax[0].axvspan(start_date, end_date, color=row['party_color'], alpha=0.3)

    ax[0].set_title('Total Debt Over Time')
    ax[0].set_xlabel('Date')
    ax[0].set_ylabel('Total Debt (in billions)')
    ax[0].legend()
    ax[0].tick_params(axis='x', rotation=45)

    # Plot debt derivative over time
    ax[1].plot(df_debt['record_date'], df_debt['debt_derivative'], 
            label=r'$\frac{d(\mathrm{Debt})}{d(\mathrm{Time})}$', 
            color='black', 
            linewidth=4)
    
    # Add background color for each party in power
    for _, row in df_prty.iterrows():
        start_date = row['record_date']
        end_date = start_date + pd.DateOffset(years=1)
        ax[1].axvspan(start_date, end_date, color=row['party_color'], alpha=0.3)

    ax[1].set_title('Debt Derivative Over Time')
    ax[1].set_xlabel('Date')
    ax[1].set_ylabel('Debt Derivative (in billions per year)')
    ax[1].legend()
    ax[1].tick_params(axis='x', rotation=45)


    plt.tight_layout()
    plt.savefig('debt_and_derivative_with_party_background.png', dpi=300)

if __name__ == "__main__":
    main()