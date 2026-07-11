/**
 * InfoDrawer.jsx
 * --------------
 * The panel that slides in from the right when a user clicks a ward.
 * Shows:
 *   - Ward name and risk score
 *   - Crime breakdown table (type, time, count)
 *   - A close button
 *
 * PROPS:
 *   wardData  — the data returned by getWardCrimes() or null if nothing selected
 *   riskScore — the risk score object for this ward from the current filter
 *   onClose   — function to call when the user closes the drawer
 *   loading   — boolean, shows a loading state while crimes are being fetched
 */

export default function InfoDrawer({ wardData, riskScore, onClose, loading }) {
  // Nothing selected — don't render anything
  if (!wardData && !loading) return null;

  // Colour for the risk badge
  const badgeColour = {
    high:   "#e74c3c",
    medium: "#f39c12",
    low:    "#27ae60",
  }[riskScore?.risk_level] ?? "#7f8c8d";

  return (
    <div style={{
      position:     "absolute",
      top:          0,
      right:        0,
      height:       "100%",
      width:        "320px",
      background:   "rgba(13, 15, 22, 0.97)",
      borderLeft:   "1px solid #2a2d3a",
      zIndex:       1000,
      overflowY:    "auto",
      padding:      "20px",
      boxShadow:    "-4px 0 20px rgba(0,0,0,0.4)",
    }}>
      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          position:     "absolute",
          top:          "14px",
          right:        "14px",
          background:   "transparent",
          border:       "none",
          color:        "#888",
          fontSize:     "20px",
          cursor:       "pointer",
          lineHeight:   1,
        }}
      >×</button>

      {/* Loading state */}
      {loading && (
        <div style={{ color: "#888", marginTop: "40px", textAlign: "center" }}>
          Loading ward data...
        </div>
      )}

      {/* Content */}
      {!loading && wardData && (
        <>
          {/* Ward name */}
          <h2 style={{ fontSize: "16px", fontWeight: 600, color: "#fff", marginBottom: "4px", paddingRight: "24px" }}>
            {wardData.ward_name}
          </h2>
          <p style={{ fontSize: "11px", color: "#555", marginBottom: "16px" }}>
            Ward {wardData.ward_code}
          </p>

          {/* Risk score badge */}
          {riskScore && (
            <div style={{
              display:       "flex",
              alignItems:    "center",
              gap:           "10px",
              background:    "#1a1d27",
              borderRadius:  "8px",
              padding:       "12px 14px",
              marginBottom:  "20px",
            }}>
              <div style={{
                width:        "10px",
                height:       "10px",
                borderRadius: "50%",
                background:   badgeColour,
                flexShrink:   0,
              }} />
              <div>
                <p style={{ fontSize: "11px", color: "#666", marginBottom: "2px" }}>Risk score</p>
                <p style={{ fontSize: "22px", fontWeight: 700, color: badgeColour, lineHeight: 1 }}>
                  {riskScore.risk_score.toFixed(1)}
                  <span style={{ fontSize: "13px", color: "#666", fontWeight: 400 }}> / 100</span>
                </p>
              </div>
              <div style={{ marginLeft: "auto" }}>
                <span style={{
                  background:   badgeColour + "22",
                  color:        badgeColour,
                  border:       `1px solid ${badgeColour}44`,
                  borderRadius: "4px",
                  padding:      "2px 8px",
                  fontSize:     "11px",
                  fontWeight:   600,
                  textTransform:"uppercase",
                }}>
                  {riskScore.risk_level}
                </span>
              </div>
            </div>
          )}

          {/* Crime breakdown table */}
          <p style={{ fontSize: "11px", color: "#555", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Crime breakdown
          </p>

          {wardData.crimes.length === 0 ? (
            <p style={{ fontSize: "13px", color: "#666" }}>No crime data for this filter.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #2a2d3a" }}>
                  <th style={{ textAlign: "left",  padding: "6px 4px", color: "#555", fontWeight: 500 }}>Type</th>
                  <th style={{ textAlign: "center",padding: "6px 4px", color: "#555", fontWeight: 500 }}>Time</th>
                  <th style={{ textAlign: "right", padding: "6px 4px", color: "#555", fontWeight: 500 }}>Count</th>
                </tr>
              </thead>
              <tbody>
                {wardData.crimes.map((crime, i) => (
                  <tr
                    key={i}
                    style={{ borderBottom: "1px solid #1a1d27" }}
                  >
                    <td style={{ padding: "7px 4px", color: "#ccc", textTransform: "capitalize" }}>
                      {crime.crime_type.replace("_", " ")}
                    </td>
                    <td style={{ padding: "7px 4px", color: "#888", textAlign: "center" }}>
                      {crime.time_of_day}
                    </td>
                    <td style={{ padding: "7px 4px", color: "#e0e0e0", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {crime.count.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <p style={{ fontSize: "10px", color: "#444", marginTop: "20px", lineHeight: 1.5 }}>
            Data is simulated based on NCRB crime categories. For demonstration purposes only.
          </p>
        </>
      )}
    </div>
  );
}