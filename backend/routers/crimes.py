"""
routers/crimes.py
-----------------
Handles GET /api/crimes/{ward_code}

Returns the full crime breakdown for a specific ward.
This is what appears when a user clicks on a ward on the map —
they see exactly which crimes happen there and when.

Example:
  GET /api/crimes/L        → crime breakdown for Kurla ward
  GET /api/crimes/M%2FE    → Govandi ward (/ must be URL-encoded as %2F)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.database import get_connection
from backend.models import CrimeDetail, CrimeList

router = APIRouter(prefix="/api/crimes", tags=["crimes"])


@router.get("/{ward_code:path}", response_model=CrimeList)
def get_ward_crimes(
    ward_code: str,
    time_of_day: Optional[str] = Query(
        default=None,
        description="Filter by 'day' or 'night'"
    ),
):
    """
    Returns all crime types recorded in a specific ward.

    The ward_code comes from the URL path — so /api/crimes/L
    returns data for ward L (Kurla / Vidyavihar).

    We also do a quick check that the ward actually exists,
    returning a 404 if not — better than returning empty data
    with no explanation.
    """
    conn = get_connection()
    try:
        # First verify the ward exists
        ward_check = conn.execute(
            "SELECT ward_name FROM wards WHERE ward_code = ?",
            (ward_code,)
        ).fetchone()

        if not ward_check:
            raise HTTPException(
                status_code=404,
                detail=f"Ward '{ward_code}' not found. Check /api/areas for valid codes."
            )

        ward_name = ward_check["ward_name"]

        # Fetch crime breakdown
        if time_of_day:
            cursor = conn.execute(
                """
                SELECT crime_type, time_of_day, count, severity
                FROM crime_summary
                WHERE ward_code = ? AND time_of_day = ?
                ORDER BY count DESC
                """,
                (ward_code, time_of_day)
            )
        else:
            cursor = conn.execute(
                """
                SELECT crime_type, time_of_day, count, severity
                FROM crime_summary
                WHERE ward_code = ?
                ORDER BY count DESC
                """,
                (ward_code,)
            )

        rows = cursor.fetchall()
        crimes = [
            CrimeDetail(
                crime_type=row["crime_type"],
                time_of_day=row["time_of_day"],
                count=row["count"],
                severity=row["severity"],
            )
            for row in rows
        ]

        return CrimeList(ward_code=ward_code, ward_name=ward_name, crimes=crimes)

    except HTTPException:
        # Re-raise HTTP exceptions as-is (don't wrap them in a 500)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()