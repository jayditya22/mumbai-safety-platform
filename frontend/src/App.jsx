/**
 * App.jsx
 * -------
 * The root component. Owns all shared state and coordinates data fetching.
 *
 * STATE:
 *   filters      — current filter values { timeOfDay, crimeType }
 *   riskScores   — array of risk scores from the API (drives map colours)
 *   selectedWard — ward_code of the clicked ward (drives InfoDrawer)
 *   wardData     — crime breakdown for selectedWard (from /api/crimes/{code})
 *   loading      — true while risk scores are being fetched
 *   drawerLoading— true while ward crime data is being fetched
 *
 * DATA FLOW:
 *   1. On mount: fetch risk scores with default filters
 *   2. On filter change: re-fetch risk scores → pass to MapView → map recolours
 *   3. On ward click: fetch crime breakdown → pass to InfoDrawer → drawer opens
 */

import { useState, useEffect } from "react";
import MapView      from "./components/MapView";
import FilterPanel  from "./components/FilterPanel";
import InfoDrawer   from "./components/InfoDrawer";
import { getRiskScores, getWardCrimes } from "./services/api";

export default function App() {
  const [filters, setFilters] = useState({
    timeOfDay: "night", // default to night — the most interesting view
    crimeType: "",
  });

  const [riskScores,    setRiskScores]    = useState([]);
  const [selectedWard,  setSelectedWard]  = useState(null);
  const [wardData,      setWardData]      = useState(null);
  const [riskScore,     setRiskScore]     = useState(null);
  const [loading,       setLoading]       = useState(true);
  const [drawerLoading, setDrawerLoading] = useState(false);

  // ── FETCH RISK SCORES whenever filters change ─────────────────────────────
  useEffect(() => {
    setLoading(true);
    getRiskScores({
      timeOfDay: filters.timeOfDay || null,
      crimeType: filters.crimeType || null,
    })
      .then(scores => {
        setRiskScores(scores);
      })
      .catch(err => {
        console.error("Failed to fetch risk scores:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [filters]); // re-run whenever filters object changes

  // ── FETCH WARD CRIMES when a ward is clicked ──────────────────────────────
  function handleWardClick(wardCode) {
    setSelectedWard(wardCode);
    setDrawerLoading(true);
    setWardData(null);

    const score = riskScores.find(s => s.ward_code === wardCode) || null;
    setRiskScore(score);

    getWardCrimes(wardCode, {
      timeOfDay: filters.timeOfDay || null,
    })
      .then(data => {
        console.log("Ward data received:", data);
        setWardData(data);
      })
      .catch(err => {
        console.error("Failed to fetch ward crimes:", err);
        setDrawerLoading(false);
      })
      .finally(() => {
        setDrawerLoading(false);
      });
  }

  function handleDrawerClose() {
    setSelectedWard(null);
    setWardData(null);
    setRiskScore(null);
  }

  function handleFilterChange(newFilters) {
    setFilters(newFilters);
    // Close the drawer when filters change — the ward data would be stale
    handleDrawerClose();
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Top filter bar */}
      <FilterPanel
        filters={filters}
        onFilterChange={handleFilterChange}
        loading={loading}
      />

      {/* Map + drawer — position relative so drawer can be absolute inside */}
      <div style={{ position: "relative", height: "calc(100vh - 50px)", overflow: "hidden" }}>
        <MapView
          riskScores={riskScores}
          onWardClick={handleWardClick}
          filters={filters}
        />
        <InfoDrawer
          wardData={wardData}
          riskScore={riskScore}
          onClose={handleDrawerClose}
          loading={drawerLoading}
        />
      </div>
    </div>
  );
}