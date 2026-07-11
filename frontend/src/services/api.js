/**
 * api.js
 * ------
 * All communication with the FastAPI backend lives here.
 *
 * WHY A SEPARATE FILE?
 * If the backend URL ever changes (e.g. when you deploy), you change
 * it in one place — not scattered across every component that needs data.
 *
 * axios.create() gives us a pre-configured instance so we never
 * have to repeat the base URL in every call.
 */

import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 10000, // 10 second timeout — fail fast rather than hang forever
});

/**
 * Fetch all 24 wards (code + name).
 * Used to populate the ward dropdown if we add one later.
 */
export async function getAreas() {
  const res = await client.get("/api/areas");
  return res.data.wards; // array of { ward_code, ward_name }
}

/**
 * Fetch risk scores for all wards.
 *
 * Both parameters are optional:
 *   getScores()                          → all wards, both time periods
 *   getScores({ timeOfDay: "night" })    → night scores only
 *   getScores({ crimeType: "theft" })    → theft-weighted scores
 *   getScores({ timeOfDay: "night", crimeType: "robbery" }) → combined
 */
export async function getRiskScores({ timeOfDay = null, crimeType = null } = {}) {
  const params = {};
  if (timeOfDay) params.time_of_day = timeOfDay;
  if (crimeType) params.crime_type  = crimeType;

  const res = await client.get("/api/risk", { params });
  return res.data.scores; // array of { ward_code, ward_name, time_of_day, risk_score, risk_level }
}

/**
 * Fetch crime breakdown for a specific ward.
 * Called when a user clicks a ward on the map.
 *
 * wardCode examples: "L", "M%2FE" (slashes need encoding but axios handles this)
 */
export async function getWardCrimes(wardCode, { timeOfDay = null } = {}) {
  const params = {};
  if (timeOfDay) params.time_of_day = timeOfDay;

  // Encode the ward code so slashes don't break the URL
  // e.g. "M/E" becomes "M%2FE" in the URL path
  const encodedCode = encodeURIComponent(wardCode);

  const res = await client.get(`/api/crimes/${encodedCode}`, { params });
  return res.data;
}