"""
models.py
---------
Pydantic models that define the shape of every API response.

WHY MODELS MATTER:
Without models, your API might return inconsistent data — sometimes
a field is missing, sometimes it's a string when it should be a number.
Pydantic models act as a contract: "this endpoint ALWAYS returns
exactly these fields with exactly these types."

FastAPI uses these models to:
  1. Validate that your database data matches what you promised
  2. Auto-generate the API documentation at /docs
  3. Serialise Python objects into clean JSON automatically
"""

from pydantic import BaseModel
from typing import List


class Ward(BaseModel):
    """
    Returned by GET /api/areas
    Basic identity of each ward — used by the frontend to build
    the dropdown list and map labels.
    """
    ward_code: str
    ward_name: str


class RiskScore(BaseModel):
    """
    Returned by GET /api/risk
    The core data the heatmap is built from.
    One row per ward per time_of_day.
    """
    ward_code:   str
    ward_name:   str
    time_of_day: str
    risk_score:  float
    risk_level:  str   # "low", "medium", or "high"


class CrimeDetail(BaseModel):
    """
    Returned by GET /api/crimes/{ward_code}
    The breakdown shown when a user clicks a ward on the map.
    """
    crime_type:  str
    time_of_day: str
    count:       int
    severity:    float


# List wrappers — FastAPI needs these to correctly document
# endpoints that return arrays of objects
class WardList(BaseModel):
    wards: List[Ward]

class RiskList(BaseModel):
    scores: List[RiskScore]

class CrimeList(BaseModel):
    ward_code: str
    ward_name: str
    crimes:    List[CrimeDetail]