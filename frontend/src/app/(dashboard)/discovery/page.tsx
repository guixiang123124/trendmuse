"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Globe,
  TrendingUp,
  Search,
  ShoppingBag,
  Filter,
  ExternalLink,
  Image as ImageIcon,
  Sparkles,
} from "lucide-react";
import GenerateDesignModal from "@/components/GenerateDesignModal";

interface TrendSignal {
  id?: string;
  title: string;
  brand?: string;
  category?: string;
  price?: number;
  image_url?: string;
  url?: string;
  source?: string;
  score?: number;
  description?: string;
  created_at?: string;
}

const API_BASE = "https://api.trendmuse.app";

const SOURCES = ["all", "scrapling", "exa", "twitter"];
const CATEGORIES = ["all", "tops", "bottoms", "dresses", "outerwear", "shoes", "accessories"];

export default function DiscoveryPage() {
  const [signals, setSignals] = useState<TrendSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState("all");
  const [category, setCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [generateSignal, setGenerateSignal] = useState<TrendSignal | null>(null);

  const fetchSignals = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (source !== "all") params.set("source", source);
      if (category !== "all") params.set("category", category);
      if (searchQuery) params.set("q", searchQuery);
      params.set("limit", "100");

      const res = await fetch(`${API_BASE}/api/discovery/trend-signals?${params}`);
      if (res.ok) {
        const data = await res.json();
        setSignals(data.signals || []);
      }
    } catch (e) {
      console.error("Failed to fetch signals:", e);
    } finally {
      setLoading(false);
    }
  }, [source, category, searchQuery]);

  useEffect(() => {
    fetchSignals();
  }, [fetchSignals]);

  const filteredSignals = signals;

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500">
            <Globe className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Trend Discovery</h1>
            <p className="text-muted-foreground">Real-time product intelligence from multiple sources</p>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-3 mt-4 max-w-xl">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchSignals()}
              placeholder="Search products and trends..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-card border border-border focus:border-primary focus:outline-none text-sm"
            />
          </div>
          <button
            onClick={fetchSignals}
            className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-6 mb-6">
        <div>
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
            <Filter className="h-3 w-3" /> Source
          </label>
          <div className="flex gap-2 mt-1">
            {SOURCES.map((s) => (
              <button
                key={s}
                onClick={() => setSource(s)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
                  source === s
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
            <ShoppingBag className="h-3 w-3" /> Category
          </label>
          <div className="flex gap-2 mt-1">
            {CATEGORIES.map((c) => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
                  category === c
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results count */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">
          {loading ? "Loading..." : `${filteredSignals.length} products found`}
        </p>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-muted-foreground">Fetching trend signals...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredSignals.length === 0 && (
        <div className="text-center py-20">
          <div className="inline-flex p-4 rounded-2xl bg-muted mb-4">
            <TrendingUp className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No products found</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Try adjusting your filters or run the Trend Scanner to scrape new data.
          </p>
        </div>
      )}

      {/* Product Grid */}
      {!loading && filteredSignals.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredSignals.map((signal, i) => (
            <div
              key={signal.id || i}
              className="rounded-2xl border border-border bg-card overflow-hidden hover:border-primary/30 transition-colors group"
            >
              {/* Image */}
              <div className="aspect-square relative bg-muted">
                {signal.image_url ? (
                  <img
                    src={signal.image_url}
                    alt={signal.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                      (e.target as HTMLImageElement).nextElementSibling?.classList.remove("hidden");
                    }}
                  />
                ) : null}
                <div className={`absolute inset-0 flex items-center justify-center ${signal.image_url ? "hidden" : ""}`}>
                  <ImageIcon className="h-10 w-10 text-muted-foreground/30" />
                </div>
                {signal.source && (
                  <span className="absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-black/60 text-white capitalize">
                    {signal.source}
                  </span>
                )}
                {signal.score != null && (
                  <span className="absolute top-2 right-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/90 text-white">
                    Score: {signal.score}
                  </span>
                )}
              </div>

              {/* Info */}
              <div className="p-4">
                <h3 className="font-medium text-sm line-clamp-2 mb-1 leading-snug">{signal.title}</h3>
                {signal.brand && (
                  <p className="text-xs text-muted-foreground mb-1">{signal.brand}</p>
                )}
                {signal.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{signal.description}</p>
                )}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {signal.price != null && (
                      <span className="text-sm font-bold text-primary">${signal.price}</span>
                    )}
                    {signal.category && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground capitalize">
                        {signal.category}
                      </span>
                    )}
                  </div>
                  {signal.url && (
                    <a
                      href={signal.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-primary transition-colors"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
                <button
                  onClick={() => setGenerateSignal(signal)}
                  className="mt-2 w-full py-2 rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 hover:opacity-90 transition-opacity"
                >
                  <Sparkles className="h-3 w-3" />
                  Generate Design
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Generate Design Modal */}
      {generateSignal && (
        <GenerateDesignModal
          signal={generateSignal}
          onClose={() => setGenerateSignal(null)}
        />
      )}
    </div>
  );
}
