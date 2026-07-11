"""
preprocess.py
-------------
Reads the raw crime CSV and produces a clean, analysis-ready version.

In a real project this script would handle:
  - Inconsistent ward name spellings
  - Missing values
  - Duplicate records
  - Outlier capping

With simulated data it's simpler, but the structure is identical to
what you'd write for real NCRB data — which is the point.
"""

import pandas as pd
import os

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
RAW_PATH   = os.path.join(BASE_DIR, "raw",       "mumbai_crimes_2023.csv")
CLEAN_PATH = os.path.join(BASE_DIR, "processed", "mumbai_crimes_clean.csv")


def load_raw(path: str) -> pd.DataFrame:
    """Load the raw CSV and do basic type enforcement."""
    df = pd.read_csv(path)

    # Enforce correct dtypes — important for SQL storage later
    df["year"]       = df["year"].astype(int)
    df["month"]      = df["month"].astype(int)
    df["hour"]       = df["hour"].astype(int)
    df["population"] = df["population"].astype(int)
    df["severity"]   = df["severity"].astype(float)
    df["base_risk"]  = df["base_risk"].astype(float)

    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning steps in sequence.
    Each step is a separate function so it's easy to add/remove rules.
    """
    df = drop_duplicates(df)
    df = validate_hour_range(df)
    df = add_time_of_day(df)
    df = drop_internal_columns(df)
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows (shouldn't exist in simulation, but good practice)."""
    before = len(df)
    df = df.drop_duplicates()
    after  = len(df)
    if before != after:
        print(f"  ! Dropped {before - after} duplicate rows")
    return df


def validate_hour_range(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hours must be 0–23. Any value outside that range means corrupted data.
    We drop those rows rather than impute — safety data should be conservative.
    """
    invalid = df[(df["hour"] < 0) | (df["hour"] > 23)]
    if len(invalid) > 0:
        print(f"  ! Dropping {len(invalid)} rows with invalid hour values")
        df = df[df["hour"].between(0, 23)]
    return df


def add_time_of_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a human-readable time_of_day label.
    This will be used by the /api/risk endpoint for time-based filtering.

    Night = 22:00 – 05:59  (the highest-risk window)
    Day   = everything else

    These cutoffs are chosen based on NCRB research showing significantly
    higher violent crime rates between 10 PM and 5 AM in urban areas.
    """
    def categorise(hour):
        if hour >= 22 or hour <= 5:
            return "night"
        else:
            return "day"

    df["time_of_day"] = df["hour"].apply(categorise)
    return df


def drop_internal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    base_risk was used to generate the data but should NOT be stored
    in the processed dataset — it would make the risk scoring trivial
    and hide the fact that we're computing scores from crime counts.
    This mimics real data where you wouldn't have a pre-labelled risk column.
    """
    return df.drop(columns=["base_risk"], errors="ignore")


def summarise(df: pd.DataFrame) -> None:
    """Print a quick sanity-check summary after cleaning."""
    print(f"\n── Clean dataset summary ─────────────────────────────")
    print(f"  Total records : {len(df):,}")
    print(f"  Wards covered : {df['ward_name'].nunique()}")
    print(f"  Crime types   : {sorted(df['crime_type'].unique())}")
    print(f"  Hours (range) : {df['hour'].min()} – {df['hour'].max()}")
    print(f"  Day / Night   : {df['time_of_day'].value_counts().to_dict()}")
    print(f"  Columns       : {list(df.columns)}")
    print(f"──────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    print("Loading raw data...")
    df = load_raw(RAW_PATH)
    print(f"  Loaded {len(df):,} rows")

    print("Cleaning...")
    df = clean(df)

    summarise(df)

    df.to_csv(CLEAN_PATH, index=False)
    print(f"✓ Clean data saved to {CLEAN_PATH}")