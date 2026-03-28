export default function Header() {
  return (
    <header
      style={{
        padding: "20px 24px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        borderBottom: "1px solid var(--border)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        background: "rgba(13,13,26,0.85)",
      }}
    >
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "10px",
          background: "linear-gradient(135deg, var(--accent), var(--accent2))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "18px",
          flexShrink: 0,
          boxShadow: "0 0 16px var(--accent-glow)",
        }}
      >
        🔍
      </div>
      <div>
        <h1
          style={{
            fontSize: "20px",
            fontWeight: 800,
            background: "linear-gradient(90deg, #a78bfa, #f472b6)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.5px",
          }}
        >
          PriceHunt
        </h1>
        <p style={{ fontSize: "11px", color: "var(--text-dim)", marginTop: "-2px" }}>
          UAE & MENA price comparison — prices in AED
        </p>
      </div>

      <div style={{ marginLeft: "auto", display: "flex", gap: "8px", flexWrap: "wrap" }}>
        {["Amazon.ae", "Noon", "Carrefour", "Sharaf DG", "Dubizzle", "OpenSooq"].map((s) => (
          <span
            key={s}
            style={{
              fontSize: "11px",
              color: "var(--text-dim)",
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "999px",
              padding: "3px 10px",
            }}
          >
            {s}
          </span>
        ))}
      </div>
    </header>
  );
}
