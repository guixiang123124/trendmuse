"use client";

import { useState, useEffect } from "react";

interface TrendSummary {
  overview: {
    total_products: number;
    total_sources: number;
    total_categories: number;
  };
  pricing: {
    avg_price: number;
    min_price: number;
    max_price: number;
  };
  by_source: Record<string, number>;
  by_category: Record<string, number>;
}

export default function TrendsPage() {
  const [summary, setSummary] = useState<TrendSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Try trends/summary first (products table)
      const res = await fetch("/api/trends/summary");
      if (res.ok) {
        const data = await res.json();
        // If products table is empty, supplement with pipeline data
        if (!data.overview?.total_products || data.overview.total_products === 0) {
          const pipelineRes = await fetch("/api/discovery/pipeline-status");
          if (pipelineRes.ok) {
            const pipeline = await pipelineRes.json();
            if (pipeline.total > 0) {
              data.overview = {
                total_products: pipeline.total,
                total_sources: Object.keys(pipeline.by_source || {}).length,
                total_categories: Object.keys(pipeline.by_source || {}).length,
              };
              data.by_source = pipeline.by_source || {};
              data.pricing = data.pricing || { avg_price: 0, min_price: 0, max_price: 0 };
            }
          }
        }
        setSummary(data);
      }
    } catch (error) {
      console.error("Error:", error);
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%)",
      padding: "2rem"
    }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "white", marginBottom: "0.5rem" }}>
          📊 Trend Analytics
        </h1>
        <p style={{ color: "#94a3b8", marginBottom: "2rem" }}>
          数据库统计和趋势分析
        </p>

        {loading ? (
          <p style={{ color: "white" }}>Loading...</p>
        ) : summary ? (
          <>
            {/* Stats Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "2rem" }}>
              <div style={{ background: "rgba(30,41,59,0.8)", borderRadius: "12px", padding: "1.5rem", border: "1px solid #334155" }}>
                <p style={{ color: "#94a3b8", fontSize: "0.875rem" }}>Total Products</p>
                <p style={{ color: "white", fontSize: "2rem", fontWeight: "bold" }}>{summary.overview.total_products.toLocaleString()}</p>
              </div>
              <div style={{ background: "rgba(30,41,59,0.8)", borderRadius: "12px", padding: "1.5rem", border: "1px solid #334155" }}>
                <p style={{ color: "#94a3b8", fontSize: "0.875rem" }}>Avg Price</p>
                <p style={{ color: "white", fontSize: "2rem", fontWeight: "bold" }}>${summary.pricing.avg_price.toFixed(2)}</p>
              </div>
              <div style={{ background: "rgba(30,41,59,0.8)", borderRadius: "12px", padding: "1.5rem", border: "1px solid #334155" }}>
                <p style={{ color: "#94a3b8", fontSize: "0.875rem" }}>Sources</p>
                <p style={{ color: "white", fontSize: "2rem", fontWeight: "bold" }}>{summary.overview.total_sources}</p>
              </div>
              <div style={{ background: "rgba(30,41,59,0.8)", borderRadius: "12px", padding: "1.5rem", border: "1px solid #334155" }}>
                <p style={{ color: "#94a3b8", fontSize: "0.875rem" }}>Categories</p>
                <p style={{ color: "white", fontSize: "2rem", fontWeight: "bold" }}>{summary.overview.total_categories}</p>
              </div>
            </div>

            {/* Sources */}
            <div style={{ background: "rgba(30,41,59,0.8)", borderRadius: "12px", padding: "1.5rem", border: "1px solid #334155", marginBottom: "2rem" }}>
              <h2 style={{ color: "white", fontSize: "1.25rem", marginBottom: "1rem" }}>📦 Products by Source</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "1rem" }}>
                {Object.entries(summary.by_source).sort((a, b) => b[1] - a[1]).map(([source, count]) => (
                  <div key={source} style={{ background: "rgba(51,65,85,0.5)", borderRadius: "8px", padding: "1rem" }}>
                    <p style={{ color: "#94a3b8", fontSize: "0.75rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {source.replace('.com', '')}
                    </p>
                    <p style={{ color: "white", fontSize: "1.5rem", fontWeight: "bold" }}>{count}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Categories */}
            <div style={{ background: "rgba(30,41,59,0.8)", borderRadius: "12px", padding: "1.5rem", border: "1px solid #334155" }}>
              <h2 style={{ color: "white", fontSize: "1.25rem", marginBottom: "1rem" }}>👗 Products by Category</h2>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {Object.entries(summary.by_category).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
                  <span key={cat} style={{ 
                    background: "rgba(139,92,246,0.3)", 
                    color: "white", 
                    padding: "0.5rem 1rem", 
                    borderRadius: "9999px",
                    fontSize: "0.875rem"
                  }}>
                    {cat} ({count})
                  </span>
                ))}
              </div>
            </div>
          </>
        ) : (
          <p style={{ color: "#ef4444" }}>Failed to load data</p>
        )}
      </div>
    </div>
  );
}
