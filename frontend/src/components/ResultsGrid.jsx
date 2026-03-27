import ResultCard from "./ResultCard";

export default function ResultsGrid({ results, loading, error, query }) {
  if (loading) {
    return (
      <div
        style={{
          maxWidth: "960px",
          margin: "32px auto 0",
          padding: "0 8px",
        }}
      >
        <div style={{ textAlign: "center", padding: "60px 0" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              border: "3px solid rgba(139,92,246,0.2)",
              borderTop: "3px solid var(--accent)",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
              margin: "0 auto 20px",
            }}
          />
          <p style={{ color: "var(--text-muted)", fontSize: "15px" }}>
            Hunting prices for <strong style={{ color: "var(--text)" }}>"{query}"</strong>...
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "13px", marginTop: "8px" }}>
            Searching eBay, Walmart, Google Shopping, Craigslist & Instagram
          </p>
          {/* Skeleton placeholders */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: "16px",
              marginTop: "32px",
              textAlign: "left",
            }}
          >
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonCard key={i} delay={i * 0.05} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: "center", padding: "60px", color: "var(--danger)" }}>
        <div style={{ fontSize: "40px", marginBottom: "16px" }}>⚠️</div>
        <p style={{ fontWeight: 600 }}>Something went wrong</p>
        <p style={{ color: "var(--text-muted)", marginTop: "8px", fontSize: "14px" }}>{error}</p>
        <p style={{ color: "var(--text-dim)", marginTop: "4px", fontSize: "13px" }}>
          Make sure the backend server is running on port 8000.
        </p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "60px" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔍</div>
        <p style={{ fontWeight: 600, fontSize: "18px" }}>No results found</p>
        <p style={{ color: "var(--text-muted)", marginTop: "8px", fontSize: "14px" }}>
          Try a different search term or check your internet connection.
        </p>
      </div>
    );
  }

  const lowestPrice = results.reduce(
    (min, r) => (r.price !== null && (min === null || r.price < min) ? r.price : min),
    null
  );

  return (
    <div
      style={{
        maxWidth: "960px",
        margin: "20px auto 0",
        padding: "0 8px",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
          gap: "16px",
        }}
      >
        {results.map((item, i) => (
          <div
            key={`${item.url}-${i}`}
            style={{ animation: `fadeIn 0.4s ease ${Math.min(i * 0.04, 0.4)}s both` }}
          >
            <ResultCard
              item={item}
              isBest={item.price !== null && item.price === lowestPrice}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function SkeletonCard({ delay }) {
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        overflow: "hidden",
        animation: `pulse 1.5s ease ${delay}s infinite`,
      }}
    >
      <div style={{ height: "160px", background: "rgba(255,255,255,0.03)" }} />
      <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ height: "14px", background: "rgba(255,255,255,0.05)", borderRadius: "4px", width: "50%" }} />
        <div style={{ height: "12px", background: "rgba(255,255,255,0.04)", borderRadius: "4px" }} />
        <div style={{ height: "12px", background: "rgba(255,255,255,0.04)", borderRadius: "4px", width: "80%" }} />
        <div style={{ height: "24px", background: "rgba(255,255,255,0.06)", borderRadius: "4px", width: "40%" }} />
      </div>
    </div>
  );
}
