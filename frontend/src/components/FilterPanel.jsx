/**
 * FilterPanel.jsx
 * ---------------
 * The top bar with two dropdowns:
 *   1. Time of day (all / day / night)
 *   2. Crime type  (all / theft / robbery / etc.)
 *
 * When the user changes either dropdown, this component calls
 * the onFilterChange prop — which triggers App.jsx to re-fetch
 * risk scores from the API with the new filters applied.
 *
 * PROPS:
 *   filters        — current filter values { timeOfDay, crimeType }
 *   onFilterChange — function to call when a filter changes
 *   loading        — boolean, disables controls while data is fetching
 */

export default function FilterPanel({ filters, onFilterChange, loading }) {
  const timeOptions = [
    { value: "",      label: "All hours" },
    { value: "day",   label: "Daytime (6am – 10pm)" },
    { value: "night", label: "Night (10pm – 6am)" },
  ];

  const crimeOptions = [
    { value: "",               label: "All crime types" },
    { value: "theft",          label: "Theft" },
    { value: "chain_snatching",label: "Chain snatching" },
    { value: "robbery",        label: "Robbery" },
    { value: "assault",        label: "Assault" },
    { value: "burglary",       label: "Burglary" },
    { value: "eve_teasing",    label: "Eve teasing" },
  ];

  const selectStyle = {
    background:   "#1a1d27",
    color:        "#e0e0e0",
    border:       "1px solid #2a2d3a",
    borderRadius: "6px",
    padding:      "6px 10px",
    fontSize:     "13px",
    cursor:       "pointer",
    outline:      "none",
    minWidth:     "180px",
    opacity:      loading ? 0.5 : 1,
  };

  return (
    <div style={{
      display:         "flex",
      alignItems:      "center",
      gap:             "16px",
      padding:         "10px 16px",
      background:      "#13151f",
      borderBottom:    "1px solid #2a2d3a",
      flexWrap:        "wrap",
    }}>
      {/* Title */}
      <span style={{ fontWeight: 600, fontSize: "14px", color: "#fff", marginRight: "8px" }}>
        🗺 Mumbai Safety Map
      </span>

      {/* Time filter */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <label style={{ fontSize: "12px", color: "#888" }}>Time</label>
        <select
          style={selectStyle}
          value={filters.timeOfDay}
          disabled={loading}
          onChange={e => onFilterChange({ ...filters, timeOfDay: e.target.value })}
        >
          {timeOptions.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Crime type filter */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <label style={{ fontSize: "12px", color: "#888" }}>Crime type</label>
        <select
          style={selectStyle}
          value={filters.crimeType}
          disabled={loading}
          onChange={e => onFilterChange({ ...filters, crimeType: e.target.value })}
        >
          {crimeOptions.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Loading indicator */}
      {loading && (
        <span style={{ fontSize: "12px", color: "#888" }}>Updating...</span>
      )}
    </div>
  );
}