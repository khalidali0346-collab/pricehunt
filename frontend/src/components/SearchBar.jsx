import { useRef } from "react";

export default function SearchBar({ onSearch, query, setQuery, location, setLocation, loading }) {
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query, location);
  };

  return (
    <div
      style={{
        maxWidth: "720px",
        margin: "40px auto 0",
        padding: "0 8px",
        animation: "fadeIn 0.5s ease",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: "28px" }}>
        <h2
          style={{
            fontSize: "clamp(24px, 5vw, 40px)",
            fontWeight: 800,
            letterSpacing: "-1px",
            background: "linear-gradient(135deg, #c4b5fd 0%, #f9a8d4 50%, #93c5fd 100%)",
            backgroundSize: "200% 200%",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            animation: "gradientShift 4s ease infinite",
          }}
        >
          Find the Best Price
        </h2>
        <p style={{ color: "var(--text-muted)", marginTop: "8px", fontSize: "15px" }}>
          We search eBay, Walmart, Google Shopping, Craigslist &amp; Instagram simultaneously
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "6px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            boxShadow: "0 0 40px rgba(139,92,246,0.08)",
            transition: "border-color 0.2s, box-shadow 0.2s",
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--accent)";
            e.currentTarget.style.boxShadow = "0 0 40px var(--accent-glow)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = "var(--border)";
            e.currentTarget.style.boxShadow = "0 0 40px rgba(139,92,246,0.08)";
          }}
        >
          {/* Item search row */}
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <span style={{ padding: "0 8px 0 12px", fontSize: "18px", opacity: 0.6 }}>🔍</span>
            <input
              ref={inputRef}
              type="text"
              placeholder="What are you looking for? e.g. iPhone 15 Pro..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--text)",
                fontSize: "16px",
                padding: "10px 0",
              }}
            />
          </div>

          {/* Location + submit row */}
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                background: "rgba(255,255,255,0.03)",
                borderRadius: "var(--radius-sm)",
                padding: "0 8px",
              }}
            >
              <span style={{ fontSize: "14px", opacity: 0.5, marginRight: "8px" }}>📍</span>
              <input
                type="text"
                placeholder="City for local results (e.g. New York)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "var(--text)",
                  fontSize: "14px",
                  padding: "8px 0",
                }}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              style={{
                background: loading
                  ? "rgba(139,92,246,0.3)"
                  : "linear-gradient(135deg, var(--accent), var(--accent2))",
                border: "none",
                borderRadius: "var(--radius-sm)",
                color: "#fff",
                fontWeight: 700,
                fontSize: "14px",
                padding: "10px 24px",
                cursor: loading || !query.trim() ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                transition: "opacity 0.2s",
                whiteSpace: "nowrap",
                boxShadow: loading ? "none" : "0 4px 16px rgba(139,92,246,0.4)",
              }}
            >
              {loading ? (
                <>
                  <span
                    style={{
                      width: "14px",
                      height: "14px",
                      border: "2px solid rgba(255,255,255,0.3)",
                      borderTop: "2px solid white",
                      borderRadius: "50%",
                      animation: "spin 0.8s linear infinite",
                      display: "inline-block",
                    }}
                  />
                  Hunting...
                </>
              ) : (
                "Hunt Prices"
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
