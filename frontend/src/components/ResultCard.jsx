const SOURCE_COLORS = {
  ebay: { bg: "rgba(234,179,8,0.15)", border: "rgba(234,179,8,0.4)", text: "#fbbf24" },
  walmart: { bg: "rgba(59,130,246,0.15)", border: "rgba(59,130,246,0.4)", text: "#60a5fa" },
  "google shopping": { bg: "rgba(34,197,94,0.15)", border: "rgba(34,197,94,0.4)", text: "#4ade80" },
  craigslist: { bg: "rgba(249,115,22,0.15)", border: "rgba(249,115,22,0.4)", text: "#fb923c" },
  instagram: { bg: "rgba(236,72,153,0.15)", border: "rgba(236,72,153,0.4)", text: "#f472b6" },
};

const SOURCE_ICONS = {
  web: "🛒",
  local: "📍",
  instagram: "📸",
};

function getSourceStyle(source) {
  const key = source.toLowerCase();
  return (
    SOURCE_COLORS[key] ||
    { bg: "rgba(139,92,246,0.15)", border: "rgba(139,92,246,0.4)", text: "#a78bfa" }
  );
}

export default function ResultCard({ item, isBest }) {
  const srcStyle = getSourceStyle(item.source);
  const icon = SOURCE_ICONS[item.source_type] || "🛒";

  const hasImage = item.image && item.image.startsWith("http");

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: "none", color: "inherit", display: "block" }}
    >
      <div
        style={{
          background: "var(--bg-card)",
          border: `1px solid ${isBest ? "rgba(139,92,246,0.6)" : "var(--border)"}`,
          borderRadius: "var(--radius)",
          overflow: "hidden",
          transition: "transform 0.2s, border-color 0.2s, box-shadow 0.2s",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          boxShadow: isBest ? "0 0 24px rgba(139,92,246,0.2)" : "none",
          cursor: "pointer",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-4px)";
          e.currentTarget.style.borderColor = "var(--border-hover)";
          e.currentTarget.style.boxShadow = "0 8px 32px rgba(139,92,246,0.2)";
          e.currentTarget.style.background = "var(--bg-card-hover)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.borderColor = isBest ? "rgba(139,92,246,0.6)" : "var(--border)";
          e.currentTarget.style.boxShadow = isBest ? "0 0 24px rgba(139,92,246,0.2)" : "none";
          e.currentTarget.style.background = "var(--bg-card)";
        }}
      >
        {/* Best price badge */}
        {isBest && (
          <div
            style={{
              position: "absolute",
              top: "10px",
              right: "10px",
              background: "linear-gradient(135deg, var(--accent), var(--accent2))",
              color: "#fff",
              fontSize: "10px",
              fontWeight: 800,
              padding: "3px 8px",
              borderRadius: "999px",
              letterSpacing: "0.5px",
              zIndex: 1,
              boxShadow: "0 2px 8px rgba(139,92,246,0.5)",
            }}
          >
            BEST PRICE
          </div>
        )}

        {/* Image */}
        <div
          style={{
            height: "160px",
            background: "rgba(255,255,255,0.02)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
            flexShrink: 0,
          }}
        >
          {hasImage ? (
            <img
              src={item.image}
              alt={item.title}
              style={{ width: "100%", height: "100%", objectFit: "contain", padding: "8px" }}
              onError={(e) => {
                e.target.style.display = "none";
                e.target.parentNode.innerHTML = `<span style="font-size:40px;opacity:0.3">${icon}</span>`;
              }}
            />
          ) : (
            <span style={{ fontSize: "40px", opacity: 0.2 }}>{icon}</span>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: "14px", flex: 1, display: "flex", flexDirection: "column", gap: "8px" }}>
          {/* Source badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              background: srcStyle.bg,
              border: `1px solid ${srcStyle.border}`,
              borderRadius: "999px",
              padding: "2px 10px",
              fontSize: "11px",
              fontWeight: 600,
              color: srcStyle.text,
              width: "fit-content",
            }}
          >
            {icon} {item.source}
          </div>

          {/* Title */}
          <p
            style={{
              fontSize: "13px",
              color: "var(--text)",
              lineHeight: 1.4,
              flex: 1,
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {item.title}
          </p>

          {/* Price */}
          <div
            style={{
              fontSize: "22px",
              fontWeight: 800,
              color: item.price !== null ? "var(--success)" : "var(--text-muted)",
            }}
          >
            {item.price !== null ? item.price_text : item.price_text}
          </div>

          {/* Meta */}
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {item.condition && (
              <MetaLine icon="✅" text={item.condition} />
            )}
            {item.location && (
              <MetaLine icon="📍" text={item.location} />
            )}
            {item.shipping && (
              <MetaLine icon="🚚" text={item.shipping} />
            )}
          </div>

          {/* CTA */}
          <div
            style={{
              marginTop: "4px",
              fontSize: "12px",
              fontWeight: 600,
              color: "var(--accent)",
              textAlign: "right",
            }}
          >
            View listing →
          </div>
        </div>
      </div>
    </a>
  );
}

function MetaLine({ icon, text }) {
  return (
    <p style={{ fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px" }}>
      <span>{icon}</span>
      <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{text}</span>
    </p>
  );
}
