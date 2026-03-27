import { useState, useCallback } from "react";
import SearchBar from "./components/SearchBar";
import FilterBar from "./components/FilterBar";
import ResultsGrid from "./components/ResultsGrid";
import PriceSummary from "./components/PriceSummary";
import Header from "./components/Header";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function App() {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [activeSource, setActiveSource] = useState("all");
  const [sortBy, setSortBy] = useState("price_asc");
  const [results, setResults] = useState([]);
  const [bestPrice, setBestPrice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);

  const handleSearch = useCallback(async (q, loc) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);

    const srcParam = activeSource === "all" ? "all" : activeSource;
    const params = new URLSearchParams({ query: q, sources: srcParam });
    if (loc) params.set("location", loc);

    try {
      const res = await fetch(`${API_BASE}/api/search?${params}`);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResults(data.results || []);
      setBestPrice(data.best_price);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message);
      setResults([]);
      setBestPrice(null);
    } finally {
      setLoading(false);
    }
  }, [activeSource]);

  const sortedResults = [...results].sort((a, b) => {
    if (sortBy === "price_asc") return (a.price ?? Infinity) - (b.price ?? Infinity);
    if (sortBy === "price_desc") return (b.price ?? -Infinity) - (a.price ?? -Infinity);
    return 0;
  });

  const filteredResults =
    activeSource === "all"
      ? sortedResults
      : sortedResults.filter((r) => r.source.toLowerCase().includes(activeSource));

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header />

      <main style={{ flex: 1, padding: "0 16px 60px" }}>
        <SearchBar
          onSearch={handleSearch}
          query={query}
          setQuery={setQuery}
          location={location}
          setLocation={setLocation}
          loading={loading}
        />

        {searched && (
          <>
            {bestPrice && <PriceSummary best={bestPrice} total={total} query={query} />}

            <FilterBar
              activeSource={activeSource}
              setActiveSource={(src) => {
                setActiveSource(src);
              }}
              sortBy={sortBy}
              setSortBy={setSortBy}
              resultCount={filteredResults.length}
            />

            <ResultsGrid
              results={filteredResults}
              loading={loading}
              error={error}
              query={query}
            />
          </>
        )}

        {!searched && <HeroHints />}
      </main>
    </div>
  );
}

function HeroHints() {
  const examples = [
    { icon: "📱", label: "iPhone 15 Pro" },
    { icon: "👟", label: "Nike Air Max" },
    { icon: "💻", label: "MacBook Air M2" },
    { icon: "🎮", label: "PS5 Controller" },
    { icon: "📷", label: "Canon EOS R50" },
    { icon: "🎧", label: "AirPods Pro" },
  ];
  return (
    <div style={{ textAlign: "center", marginTop: "60px", animation: "fadeIn 0.6s ease" }}>
      <p style={{ color: "var(--text-muted)", marginBottom: "24px", fontSize: "15px" }}>
        Try searching for...
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center", maxWidth: "520px", margin: "0 auto" }}>
        {examples.map((e) => (
          <span
            key={e.label}
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "999px",
              padding: "8px 18px",
              fontSize: "14px",
              cursor: "default",
              color: "var(--text-muted)",
            }}
          >
            {e.icon} {e.label}
          </span>
        ))}
      </div>

      <div style={{ display: "flex", gap: "32px", justifyContent: "center", marginTop: "60px", flexWrap: "wrap" }}>
        {[
          { icon: "🛒", title: "eBay", desc: "Buy it now listings" },
          { icon: "🏪", title: "Walmart", desc: "Retail store prices" },
          { icon: "🔍", title: "Google Shopping", desc: "Compare across stores" },
          { icon: "📍", title: "Craigslist", desc: "Local real-world prices" },
          { icon: "📸", title: "Instagram", desc: "Social commerce posts" },
        ].map((s) => (
          <div key={s.title} style={{ textAlign: "center", width: "100px" }}>
            <div style={{ fontSize: "28px", marginBottom: "8px" }}>{s.icon}</div>
            <div style={{ fontWeight: 600, fontSize: "13px", marginBottom: "4px" }}>{s.title}</div>
            <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>{s.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
