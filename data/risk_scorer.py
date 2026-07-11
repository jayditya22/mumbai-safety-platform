"""
risk_scorer.py
--------------
Reads the clean crime CSV, computes a 0–100 risk score for each ward,
and writes everything into a SQLite database for the backend to query.

THE SCORING FORMULA (important — you should be able to explain this):

  raw_score = Σ (crime_count × severity_weight) / population × time_multiplier

  Where:
    - crime_count      = number of incidents of a given type in a ward
    - severity_weight  = how serious that crime type is (0.5 for theft → 1.0 for assault)
    - population       = ward population (prevents dense wards from scoring unfairly high)
    - time_multiplier  = 1.4 if night hours, 1.0 if day hours

  After computing raw scores for all wards, we apply MIN-MAX NORMALISATION:
    normalised = (score - min_score) / (max_score - min_score) × 100

  This stretches scores so the safest ward = 0 and the riskiest = 100,
  making the heatmap visually meaningful regardless of absolute crime volumes.
"""

import pandas as pd
import numpy as np
import sqlite3
import os

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
CLEAN_PATH = os.path.join(BASE_DIR, "processed", "mumbai_crimes_clean.csv")
DB_PATH    = os.path.join(BASE_DIR, "..",         "mumbai_safety.db")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
# Night hours are defined as 22:00–05:59.
# Crimes in this window get a 1.4× multiplier because:
#  (a) they represent greater danger to pedestrians / commuters
#  (b) response times are slower
#  (c) NCRB data consistently shows higher severity outcomes at night
NIGHT_MULTIPLIER = 1.4
DAY_MULTIPLIER   = 1.0

# Risk buckets — used to assign a human-readable label
def risk_level(score: float) -> str:
    if score >= 67:
        return "high"
    elif score >= 34:
        return "medium"
    else:
        return "low"


def compute_raw_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the weighted crime burden for each ward × time_of_day combination.

    We're essentially asking: "Given this ward's population, how much
    weighted crime exposure does a person face here?"
    """
    # Apply time multiplier as a new column
    df = df.copy()
    df["time_multiplier"] = df["time_of_day"].map({
        "night": NIGHT_MULTIPLIER,
        "day":   DAY_MULTIPLIER,
    })

    # Weighted contribution of each individual record:
    #   severity × time_multiplier (the count is 1 per row — each row IS one incident)
    df["weighted_incident"] = df["severity"] * df["time_multiplier"]

    # Aggregate: sum weighted incidents per ward per time_of_day
    agg = (
        df.groupby(["ward_code", "ward_name", "time_of_day", "population"])
        ["weighted_incident"]
        .sum()
        .reset_index()
        .rename(columns={"weighted_incident": "weighted_sum"})
    )

    # Divide by population (per 100k) so large wards aren't penalised
    agg["raw_score"] = agg["weighted_sum"] / (agg["population"] / 100_000)

    return agg


def normalise(scores: pd.Series) -> pd.Series:
    """
    Min-max normalisation: squishes all values into [0, 100].

    Why min-max and not z-score?
    - Min-max gives a bounded output (always 0–100) — perfect for a colour scale
    - Z-score gives unbounded output (negative scores, values > 100) — awkward for a map
    - The tradeoff: min-max is sensitive to outliers. With 24 wards this is fine.
    """
    min_s = scores.min()
    max_s = scores.max()
    if max_s == min_s:
        return pd.Series([50.0] * len(scores), index=scores.index)
    return ((scores - min_s) / (max_s - min_s) * 100).round(2)


def build_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produces the main risk scores table:
      ward_code | ward_name | time_of_day | risk_score | risk_level
    """
    agg = compute_raw_scores(df)

    # Normalise scores WITHIN each time_of_day group
    # (so day scores and night scores are each normalised independently)
    agg["risk_score"] = (
        agg.groupby("time_of_day")["raw_score"]
        .transform(normalise)
    )

    agg["risk_level"] = agg["risk_score"].apply(risk_level)

    return agg[["ward_code", "ward_name", "time_of_day", "risk_score", "risk_level"]]


def build_crime_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produces the per-ward crime breakdown table:
      ward_code | ward_name | crime_type | time_of_day | count | severity

    This powers the /api/crimes/{ward} endpoint — when a user clicks
    a ward on the map, they see this breakdown.
    """
    summary = (
        df.groupby(["ward_code", "ward_name", "crime_type", "time_of_day", "severity"])
        .size()
        .reset_index(name="count")
    )
    return summary


def write_to_sqlite(risk_df: pd.DataFrame, crime_df: pd.DataFrame, db_path: str) -> None:
    """
    Writes both tables into SQLite. Creates the database file if it doesn't exist.

    We use if_exists='replace' so re-running this script refreshes the DB cleanly.
    In production you'd want migrations, but for this project a full refresh is fine.
    """
    conn = sqlite3.connect(db_path)

    risk_df.to_sql("risk_scores",    conn, if_exists="replace", index=False)
    crime_df.to_sql("crime_summary",  conn, if_exists="replace", index=False)

    # Also store ward metadata (distinct wards with population)
    wards_df = (
        risk_df[["ward_code", "ward_name"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    wards_df.to_sql("wards", conn, if_exists="replace", index=False)

    conn.close()
    print(f"✓ Database written to {db_path}")


def print_summary(risk_df: pd.DataFrame) -> None:
    print("\n── Risk score preview ────────────────────────────────")
    night = risk_df[risk_df["time_of_day"] == "night"].sort_values("risk_score", ascending=False)
    print("\nTop 5 riskiest wards at night:")
    print(night[["ward_name", "risk_score", "risk_level"]].head().to_string(index=False))

    print("\nTop 5 safest wards at night:")
    print(night[["ward_name", "risk_score", "risk_level"]].tail().to_string(index=False))
    print("──────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    print("Loading clean data...")
    df = pd.read_csv(CLEAN_PATH)
    print(f"  Loaded {len(df):,} rows")

    print("Computing risk scores...")
    risk_df = build_risk_table(df)

    print("Building crime summary...")
    crime_df = build_crime_summary(df)

    print_summary(risk_df)

    print("Writing to SQLite database...")
    write_to_sqlite(risk_df, crime_df, DB_PATH)

    print("\n✓ Module 1 complete. Database is ready for the backend.")