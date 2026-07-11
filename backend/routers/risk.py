from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.database import get_connection
from backend.models import RiskScore, RiskList
from collections import defaultdict

router = APIRouter(prefix="/api/risk", tags=["risk"])

NIGHT_MULTIPLIER = 1.4
DAY_MULTIPLIER   = 1.0


def risk_level(score: float) -> str:
    if score >= 67:
        return "high"
    elif score >= 34:
        return "medium"
    else:
        return "low"


def normalise(values: list) -> list:
    min_r, max_r = min(values), max(values)
    if max_r == min_r:
        return [50.0] * len(values)
    return [round((v - min_r) / (max_r - min_r) * 100, 2) for v in values]


@router.get("", response_model=RiskList)
def get_risk_scores(
    time_of_day: Optional[str] = Query(default=None),
    crime_type: Optional[str] = Query(default=None),
):
    conn = get_connection()
    try:
        if crime_type:
            scores = _get_scores_filtered_by_crime(conn, crime_type, time_of_day)
        else:
            scores = _get_precomputed_scores(conn, time_of_day)
        return RiskList(scores=scores)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


def _get_precomputed_scores(conn, time_of_day):
    if time_of_day:
        cursor = conn.execute(
            "SELECT ward_code, ward_name, time_of_day, risk_score, risk_level FROM risk_scores WHERE time_of_day = ? ORDER BY risk_score DESC",
            (time_of_day,)
        )
    else:
        cursor = conn.execute(
            "SELECT ward_code, ward_name, time_of_day, risk_score, risk_level FROM risk_scores ORDER BY risk_score DESC"
        )
    rows = cursor.fetchall()
    return [
        RiskScore(
            ward_code=row["ward_code"],
            ward_name=row["ward_name"],
            time_of_day=row["time_of_day"],
            risk_score=row["risk_score"],
            risk_level=row["risk_level"],
        )
        for row in rows
    ]


def _get_scores_filtered_by_crime(conn, crime_type, time_of_day):
    if time_of_day:
        cursor = conn.execute(
            "SELECT ward_code, ward_name, crime_type, time_of_day, count, severity FROM crime_summary WHERE crime_type = ? AND time_of_day = ?",
            (crime_type, time_of_day)
        )
    else:
        cursor = conn.execute(
            "SELECT ward_code, ward_name, crime_type, time_of_day, count, severity FROM crime_summary WHERE crime_type = ?",
            (crime_type,)
        )
    rows = cursor.fetchall()
    if not rows:
        return []

    ward_scores = defaultdict(lambda: {"ward_name": "", "time_of_day": "", "raw": 0.0})
    for row in rows:
        key = (row["ward_code"], row["time_of_day"])
        multiplier = NIGHT_MULTIPLIER if row["time_of_day"] == "night" else DAY_MULTIPLIER
        ward_scores[key]["ward_name"] = row["ward_name"]
        ward_scores[key]["time_of_day"] = row["time_of_day"]
        ward_scores[key]["raw"] += row["count"] * row["severity"] * multiplier

    raw_values = [v["raw"] for v in ward_scores.values()]
    normalised = normalise(raw_values)

    results = []
    for (ward_code, tod), data, score in zip(ward_scores.keys(), ward_scores.values(), normalised):
        results.append(RiskScore(
            ward_code=ward_code,
            ward_name=data["ward_name"],
            time_of_day=tod,
            risk_score=score,
            risk_level=risk_level(score),
        ))

    results.sort(key=lambda x: x.risk_score, reverse=True)
    return results