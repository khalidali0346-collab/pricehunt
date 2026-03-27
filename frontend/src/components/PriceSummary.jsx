export default function PriceSummary({ best, total, query }) {
  return (
    <div
      style={{
        maxWidth: "720px",
        margin: "28px auto 0",
        padding: "0 8px",
        animation: "fadeIn 0.4s ease",
      }}
    >
      <div
        style={{
          background: "linear-gradient(135deg, rgba(139,92,246,0.15), rgba(236,72,153,0.1))",
          border: "1px solid rgba(139,92,246,0.35)",
          borderRadius: "var(--radius)",
          padding: "20px 24px",
          display: "flex",
          alignItems: "center",
          gap: "20px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: "160px" }}>
          <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "1px" }}>
            Best Price Found
          </p>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span
              style={{
                fontSize: "36px",
                fontWeight: 800,
                background: "linear-gradient(90deg, #a78bfa, #f472b6)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {best.price_text}
            </span>
            <span
              style={{
                fontSize: "13px",
                background: "rgba(139,92,246,0.2)",
                border: "1px solid rgba(139,92,246,0.3)",
                borderRadius: "999px",
                padding: "2px 10px",
                color: "#c4b5fd",
              }}
            >
              {best.source}
            </span>
          </div>
        </div>

        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
          <Stat label="Results Found" value={total} />
          <Stat label="Best From" value={best.source} />
          <div>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "1px" }}>
              View Deal
            </p>
            <a
              href={best.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-block",
                background: "linear-gradient(135deg, var(--accent), var(--accent2))",
                color: "#fff",
                textDecoration: "none",
                fontWeight: 700,
                fontSize: "13px",
                padding: "8px 18px",
                borderRadius: "var(--radius-sm)",
                boxShadow: "0 4px 16px rgba(139,92,246,0.35)",
              }}
            >
              Go to Listing →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "1px" }}>
        {label}
      </p>
      <p style={{ fontSize: "20px", fontWeight: 700, color: "var(--text)" }}>{value}</p>
    </div>
  );
}
