"""
routers/areas.py
----------------
Handles GET /api/areas

Returns the list of all 24 wards. The frontend uses this to
populate any dropdown menus and to know which ward codes exist.
"""

from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.models import Ward, WardList

# APIRouter is like a mini FastAPI app — it holds a group of related routes.
# We set prefix="/api/areas" so every route defined here automatically
# starts with that path. The main.py file assembles all routers together.
router = APIRouter(prefix="/api/areas", tags=["areas"])


@router.get("", response_model=WardList)
def get_all_areas():
    """
    Returns all 24 Mumbai wards with their codes and names.

    The response_model=WardList argument tells FastAPI:
      - Validate the output matches WardList before sending
      - Include this endpoint in /docs with the correct schema shown
    """
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT ward_code, ward_name FROM wards ORDER BY ward_code")
        rows = cursor.fetchall()

        # sqlite3.Row objects aren't directly serialisable — we convert
        # each row into a Ward Pydantic model first
        wards = [Ward(ward_code=row["ward_code"], ward_name=row["ward_name"]) for row in rows]
        return WardList(wards=wards)

    except Exception as e:
        # If something goes wrong (e.g. DB not found), return a proper
        # HTTP 500 error with a message — not a raw Python traceback
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Always close the connection, even if an error occurred
        conn.close()