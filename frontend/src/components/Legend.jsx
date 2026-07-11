export default function Legend() {
  return (
    <div style={{
      position:     "absolute",
      bottom:       "30px",
      left:         "10px",
      zIndex:       1000,
      background:   "rgba(15, 17, 23, 0.92)",
      border:       "1px solid #2a2d3a",
      borderRadius: "8px",
      padding:      "12px 16px",
      minWidth:     "160px",
    }}>
      <p style={{ fontSize: "11px", color: "#888", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Risk level
      </p>

      {/* Continuous gradient bar */}
      <div style={{
        width:        "100%",
        height:       "12px",
        borderRadius: "6px",
        background:   "linear-gradient(to right, #DCE000, #E06C00, #E02B00)",
        marginBottom: "4px",
      }} />

      {/* Labels below the bar */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span style={{ fontSize: "10px", color: "#DCE000" }}>Low</span>
        <span style={{ fontSize: "10px", color: "#E06C00" }}>Medium</span>
        <span style={{ fontSize: "10px", color: "#E02B00" }}>High</span>
      </div>

      {/* No data indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "10px" }}>
        <div style={{ width: "12px", height: "12px", borderRadius: "3px", background: "#2c3e50", flexShrink: 0 }} />
        <span style={{ fontSize: "11px", color: "#666" }}>No data</span>
      </div>
    </div>
  );
}