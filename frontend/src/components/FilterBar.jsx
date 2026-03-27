const SOURCES = [
  { id: "all", label: "All Sources", icon: "⚡" },
  { id: "ebay", label: "eBay", icon: "🛒" },
  { id: "walmart", label: "Walmart", icon: "🏪" },
  { id: "google", label: "Google Shopping", icon: "🔍" },
  { id: "craigslist", label: "Craigslist", icon: "📍" },
  { id: "instagram", label: "Instagram", icon: "📸" },
];

const SORT_OPTIONS = [
  { id: "price_asc", label: "Price: Low → High" },
  { id: "price_desc", label: "Price: High → Low" },
];

export default function FilterBar({ activeSource, setActiveSource, sortBy, setSortBy, resultCount }) {
  return (
    <div
      style={{
        maxWidth: "960px",
        margin: "24px auto 0",
        padding: "0 8px",
        animation: "fadeIn 0.4s ease 0.1s both",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
          justifyContent: "space-between",
        }}
      >
        {/* Source filters */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {SOURCES.map((src) => {
            const active = activeSource === src.id;
            return (
              <button
                key={src.id}
                onClick={() => setActiveSource(src.id)}
                style={{
                  background: active
                    ? "linear-gradient(135deg, var(--accent), var(--accent2))"
                    : "var(--bg-card)",
                  border: `1px solid ${active ? "transparent" : "var(--border)"}`,
                  borderRadius: "999px",
                  color: active ? "#fff" : "var(--text-muted)",
                  fontSize: "13px",
                  fontWeight: active ? 700 : 400,
                  padding: "6px 14px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: active ? "0 4px 12px rgba(139,92,246,0.35)" : "none",
                }}
              >
                {src.icon} {src.label}
              </button>
            );
          })}
        </div>

        {/* Right side: result count + sort */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            {resultCount} result{resultCount !== 1 ? "s" : ""}
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text)",
              fontSize: "13px",
              padding: "6px 10px",
              cursor: "pointer",
              outline: "none",
            }}
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
