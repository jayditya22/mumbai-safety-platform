"""
generate_data.py
----------------
Generates a realistic simulated crime dataset for Mumbai's 24 wards.

WHY SIMULATED?
Real ward-level crime data from NCRB (National Crime Records Bureau) is
published only at city/district level in PDF format — not machine-readable
and not ward-specific. This script generates data that mirrors NCRB crime
categories and realistic ward-level risk patterns. The platform is designed
so real data can replace this file at any point.
"""

import pandas as pd
import numpy as np
import os

# ── 1. SEED ───────────────────────────────────────────────────────────────────
# Setting a seed means every run produces IDENTICAL data.
# This is important for reproducibility — your risk scores won't shift
# every time someone runs the script.
np.random.seed(42)

# ── 2. MUMBAI'S 24 WARDS ──────────────────────────────────────────────────────
# Mumbai is divided into 24 administrative wards by the BMC
# (Brihanmumbai Municipal Corporation). Each ward has:
#   - a base_risk:  float between 0 and 1 reflecting how crime-prone
#                   the area is relative to others (based on news reports,
#                   socioeconomic indicators, population density)
#   - a population: approximate residential population (used as denominator
#                   in risk scoring so dense wards aren't unfairly penalised)
WARDS = [
    {"ward": "A",  "name": "Colaba / Fort",           "base_risk": 0.45, "population": 150000},
    {"ward": "B",  "name": "Mandvi / Dongri",         "base_risk": 0.70, "population": 210000},
    {"ward": "C",  "name": "Mumbadevi / Bhuleshwar",  "base_risk": 0.65, "population": 190000},
    {"ward": "D",  "name": "Malabar Hill / Tardeo",   "base_risk": 0.25, "population": 120000},
    {"ward": "E",  "name": "Byculla / Mazgaon",       "base_risk": 0.68, "population": 230000},
    {"ward": "F/N","name": "Sion / Dharavi",           "base_risk": 0.82, "population": 340000},
    {"ward": "F/S","name": "Worli / Prabhadevi",      "base_risk": 0.38, "population": 180000},
    {"ward": "G/N","name": "Dharavi / Matunga",       "base_risk": 0.78, "population": 310000},
    {"ward": "G/S","name": "Dadar / Mahim",           "base_risk": 0.55, "population": 260000},
    {"ward": "H/E","name": "Bandra East / Kurla",     "base_risk": 0.72, "population": 290000},
    {"ward": "H/W","name": "Bandra West",              "base_risk": 0.30, "population": 175000},
    {"ward": "K/E","name": "Andheri East / Kurla",    "base_risk": 0.75, "population": 420000},
    {"ward": "K/W","name": "Andheri West / Juhu",     "base_risk": 0.35, "population": 390000},
    {"ward": "L",  "name": "Kurla / Vidyavihar",      "base_risk": 0.80, "population": 450000},
    {"ward": "M/E","name": "Govandi / Mankhurd",      "base_risk": 0.88, "population": 480000},
    {"ward": "M/W","name": "Chembur",                  "base_risk": 0.58, "population": 310000},
    {"ward": "N",  "name": "Ghatkopar",                "base_risk": 0.62, "population": 370000},
    {"ward": "P/N","name": "Goregaon / Malad North",  "base_risk": 0.55, "population": 410000},
    {"ward": "P/S","name": "Malad South / Kandivali",  "base_risk": 0.50, "population": 390000},
    {"ward": "R/C","name": "Dahisar / Kandivali North","base_risk": 0.48, "population": 360000},
    {"ward": "R/N","name": "Dahisar North",            "base_risk": 0.44, "population": 290000},
    {"ward": "R/S","name": "Borivali",                 "base_risk": 0.42, "population": 330000},
    {"ward": "S",  "name": "Bhandup / Mulund",        "base_risk": 0.52, "population": 350000},
    {"ward": "T",  "name": "Mulund",                   "base_risk": 0.46, "population": 280000},
]

# ── 3. CRIME TYPES ────────────────────────────────────────────────────────────
# Based on NCRB categories relevant to urban public safety.
# Each has a severity_weight used in risk scoring (defined in risk_scorer.py)
# and a base_rate = how many incidents per 100k population per year on average.
CRIME_TYPES = [
    {"type": "theft",          "severity": 0.50, "base_rate": 180},
    {"type": "chain_snatching","severity": 0.85, "base_rate":  80},
    {"type": "robbery",        "severity": 1.00, "base_rate":  40},
    {"type": "assault",        "severity": 1.00, "base_rate":  55},
    {"type": "burglary",       "severity": 0.70, "base_rate":  60},
    {"type": "eve_teasing",    "severity": 0.60, "base_rate":  70},
]

# ── 4. TIME DISTRIBUTION ──────────────────────────────────────────────────────
# Crime is not uniformly distributed across the day.
# This array has 24 values (one per hour, 0–23) representing the
# RELATIVE probability of a crime happening in that hour.
# Night hours (20:00–03:00) are weighted higher — consistent with
# NCRB observations on time-of-day crime patterns.
HOUR_WEIGHTS = np.array([
    0.5, 0.4, 0.5, 0.4, 0.3, 0.3,  # 00–05: late night, low activity
    0.4, 0.7, 1.0, 1.1, 1.2, 1.2,  # 06–11: morning rush rising
    1.3, 1.2, 1.1, 1.2, 1.3, 1.4,  # 12–17: afternoon / evening peak
    1.5, 1.6, 1.4, 1.2, 0.9, 0.7,  # 18–23: peak crime window
])
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()  # normalise to probabilities

# ── 5. GENERATE RECORDS ───────────────────────────────────────────────────────
# For each ward × crime type combination, we simulate how many incidents
# happened in each month of 2023, then assign each incident a random hour
# drawn from our time distribution above.
records = []

YEAR = 2023
MONTHS = range(1, 13)

for ward in WARDS:
    for crime in CRIME_TYPES:
        # Expected annual count for this ward + crime type:
        #   (base_rate per 100k) × (population / 100k) × ward_risk_multiplier
        # We then add Poisson noise — a standard statistical technique for
        # modelling count data (number of events in a time period).
        # Poisson noise means some months will naturally be higher/lower,
        # just like real crime data.
        annual_expected = (
            crime["base_rate"]
            * (ward["population"] / 100_000)
            * ward["base_risk"]
        )

        for month in MONTHS:
            # Distribute the annual count across months with slight variance
            monthly_count = int(np.random.poisson(annual_expected / 12))

            for _ in range(monthly_count):
                # Assign each incident a random hour of day
                hour = np.random.choice(24, p=HOUR_WEIGHTS)
                records.append({
                    "ward_code":    ward["ward"],
                    "ward_name":    ward["name"],
                    "crime_type":   crime["type"],
                    "severity":     crime["severity"],
                    "year":         YEAR,
                    "month":        month,
                    "hour":         int(hour),
                    "population":   ward["population"],
                    "base_risk":    ward["base_risk"],   # kept for validation only
                })

# ── 6. SAVE ───────────────────────────────────────────────────────────────────
df = pd.DataFrame(records)

output_path = os.path.join(os.path.dirname(__file__), "raw", "mumbai_crimes_2023.csv")
df.to_csv(output_path, index=False)

print(f"✓ Generated {len(df):,} crime records across {len(WARDS)} wards")
print(f"✓ Saved to {output_path}")
print(f"\nSample (first 5 rows):")
print(df.head().to_string(index=False))
print(f"\nCrime type distribution:")
print(df["crime_type"].value_counts().to_string())