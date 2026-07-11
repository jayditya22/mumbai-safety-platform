/**
 * MapView.jsx
 * -----------
 * The interactive Leaflet map. This is the centrepiece of the application.
 *
 * What this component does:
 *   1. Loads the Mumbai ward GeoJSON from the public/ folder
 *   2. Colours each ward polygon based on its risk score
 *   3. Shows a tooltip on hover with ward name and risk score
 *   4. Fires onWardClick when a user clicks a ward
 *
 * PROPS:
 *   riskScores   — array from getRiskScores() — drives the colouring
 *   onWardClick  — called with ward_code when a ward is clicked
 *   filters      — current filter state (used to pick day vs night scores)
 *
 * KEY CONCEPTS:
 *   - GeoJSON: a standard JSON format for geographic shapes (polygons, points, lines)
 *   - Choropleth map: a map where areas are coloured by a data value — exactly what we're building
 *   - Leaflet layers: each ward polygon is a Leaflet "layer" we style and add event listeners to
 */

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import Legend from "./Legend";
// Lookup table: GeoJSON ward code → full ward name
// The GeoJSON only has codes (A, P/N, etc.) so we map them manually
const WARD_NAMES = {
  "A":   "Colaba / Fort",
  "B":   "Mandvi / Dongri",
  "C":   "Mumbadevi / Bhuleshwar",
  "D":   "Malabar Hill / Tardeo",
  "E":   "Byculla / Mazgaon",
  "F/N": "Sion / Dharavi",
  "F/S": "Worli / Prabhadevi",
  "G/N": "Dharavi / Matunga",
  "G/S": "Dadar / Mahim",
  "H/E": "Bandra East / Kurla",
  "H/W": "Bandra West",
  "K/E": "Andheri East / Kurla",
  "K/W": "Andheri West / Juhu",
  "L":   "Kurla / Vidyavihar",
  "M/E": "Govandi / Mankhurd",
  "M/W": "Chembur",
  "N":   "Ghatkopar",
  "P/N": "Goregaon / Malad North",
  "P/S": "Malad South / Kandivali",
  "R/C": "Dahisar / Kandivali North",
  "R/N": "Dahisar North",
  "R/S": "Borivali",
  "S":   "Bhandup / Mulund",
  "T":   "Mulund",
};

// ── COLOUR LOGIC ──────────────────────────────────────────────────────────────
// Converts a 0-100 risk score to a smooth colour gradient
// 0   = low    (#DCE000)
// 50  = medium (#E06C00)
// 100 = high   (#E02B00)
function riskColour(score) {
  if (score === null || score === undefined) return "#2c3e50"; // no data

  // Clamp score between 0 and 100
  const s = Math.max(0, Math.min(100, score));

  let r, g, b;

  if (s <= 50) {
    // Low (#DCE000) to Medium (#E06C00)
    const t = s / 50;
    r = Math.round(220 + t * (224 - 220)); // 220 → 224
    g = Math.round(224 + t * (108 - 224)); // 224 → 108
    b = Math.round(0   + t * (0   - 0));   // 0 → 0
  } else {
    // Medium (#E06C00) to High (#E02B00)
    const t = (s - 50) / 50;
    r = Math.round(224 + t * (224 - 224)); // 224 → 224
    g = Math.round(108 + t * (43  - 108)); // 108 → 43
    b = Math.round(0   + t * (0   - 0));   // 0 → 0
  }

  return `rgb(${r},${g},${b})`;
}

// Opacity also scales with risk — high risk areas are more vivid
function riskOpacity(score) {
  if (score === null || score === undefined) return 0.25;
  const s = Math.max(0, Math.min(100, score));
  // Ranges from 0.35 (safest) to 0.80 (riskiest)
  return 0.35 + (s / 100) * 0.45;
}

export default function MapView({ riskScores, onWardClick, filters }) {
  const mapRef     = useRef(null); // reference to the Leaflet map instance
  const mapDivRef  = useRef(null); // reference to the <div> the map renders into
  const geoLayerRef= useRef(null); // reference to the GeoJSON layer so we can update it
  const scoreMapRef = useRef({});

  // Build a lookup: ward_code → risk score object
  // This lets us colour each ward in O(1) instead of searching the array each time
  const scoreMap = {};
  (riskScores || []).forEach(s => {
    // When both day and night are returned, prefer the one matching the current filter
    // If no filter, we average them — or just take the last one (they're similar)
    scoreMap[s.ward_code] = s;
    scoreMapRef.current = scoreMap;
  });

  // ── INITIALISE MAP (runs once on mount) ────────────────────────────────────
  useEffect(() => {
    // Guard: don't initialise twice
    if (mapRef.current) return;

    // Create the Leaflet map centred on Mumbai
    // 19.076, 72.877 are Mumbai's approximate lat/lng coordinates
    const map = L.map(mapDivRef.current, {
      center:       [19.076, 72.877],
      zoom:         11,
      zoomControl:  true,
    });

    // Add OpenStreetMap tiles as the base layer
    // We use a dark variant from CartoDB that matches our dark UI theme
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_matter/{z}/{x}/{y}{r}.png",
      {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 19,
      }
    ).addTo(map);

    mapRef.current = map;

    // Load the ward GeoJSON from public/
    fetch("/ward_boundaries.geojson")
      .then(r => r.json())
      .then(geojson => {
        addGeoJsonLayer(map, geojson, scoreMap);
      })
      .catch(err => {
        console.error("Failed to load ward boundaries GeoJSON:", err);
      });

    // Cleanup: remove the map when the component unmounts
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []); // empty deps = run once on mount

  // ── UPDATE COLOURS when riskScores changes ────────────────────────────────
  // When the user changes a filter, riskScores is updated by App.jsx.
  // We need to re-colour every ward without re-creating the whole map.
  useEffect(() => {
    if (!geoLayerRef.current) return;

    // Rebuild the score lookup with fresh data
    const freshMap = {};
    (riskScores || []).forEach(s => { freshMap[s.ward_code] = s; });

    // Iterate over every layer (ward polygon) and update its style
    geoLayerRef.current.eachLayer(layer => {
      const wardCode = getWardCode(layer.feature);
      const score    = freshMap[wardCode]?.risk_score ?? null;
      layer.setStyle({
        fillColor:   riskColour(score),
        fillOpacity: riskOpacity(score),
        color:       "#ffffff",
        weight:      0.8,
        opacity:     0.4,
      });
    });
  }, [riskScores]);

  // ── HELPER: add the GeoJSON layer to the map ───────────────────────────────
  function addGeoJsonLayer(map, geojson, scoreMap) {
    const layer = L.geoJSON(geojson, {
      style: feature => {
        const wardCode = getWardCode(feature);
        const score    = scoreMap[wardCode]?.risk_score ?? null;
        return {
          fillColor:   riskColour(score),
          fillOpacity: riskOpacity(score),
          color:       "#ffffff",
          weight:      0.8,
          opacity:     0.4,
        };
      },

      onEachFeature: (feature, layer) => {
        const wardCode = getWardCode(feature);
        const wardName = getWardName(feature);

        layer.on("mouseover", function (e) {
          this.setStyle({ weight: 2.5, color: "#ffffff", opacity: 1 });
          
          const tooltipScore = scoreMapRef.current[wardCode];
          
          this.bindTooltip(
            `<strong>${wardName}</strong><br/>` +
            (tooltipScore
              ? `Risk: <strong>${tooltipScore.risk_score.toFixed(1)}</strong> / 100 &nbsp;(${tooltipScore.risk_level})`
              : "No data"),
            { sticky: true }
          ).openTooltip(e.latlng);
        });

        layer.on("mouseout", function () {
          layer.closeTooltip();
          // Restore from the layer's own stored style — not a stale closure
          this.setStyle({
            weight:  0.8,
            color:   "#ffffff",
            opacity: 0.4,
          });
        });

        layer.on("click", function () {
          onWardClick(wardCode);
        });
      },
    }).addTo(map);

    geoLayerRef.current = layer;
    map.fitBounds(layer.getBounds(), { padding: [20, 20] });
  }

  // ── HELPERS: extract ward code and name from GeoJSON feature ──────────────
  // GeoJSON from DataMeet uses different property names than our DB ward codes.
  // We try common property names and fall back to whatever is available.
  function getWardCode(feature) {
  const p = feature.properties;
  return p.name || p.ward_no || p.WARD_NO || p.ward_code || "";
}

function getWardName(feature) {
  const code = getWardCode(feature);
  return WARD_NAMES[code] || code;
}

  return (
    <div style={{ position: "relative", width: "100%", height: "calc(100vh - 50px)" }}>
      <div
        ref={mapDivRef}
        style={{ width: "100%", height: "100%", minHeight: "500px" }}
      />
      <Legend />
    </div>
  );
}