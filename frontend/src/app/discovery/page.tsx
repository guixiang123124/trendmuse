"use client";

import { useState, useEffect } from "react";
import {
  Globe,
  TrendingUp,
  Flame,
  Search,
  ShoppingBag,
  Palette,
  ArrowUpRight,
  ArrowRight,
  BarChart3,
  Shirt,
  Layers,
} from "lucide-react";

interface TrendItem {
  name: string;
  score: number;
  direction: string;
  description?: string;
  hex?: string;
}

interface TrendProduct {
  rank: number;
  name: string;
  category: string;
  price: number;
  rating: number;
  reviews: number;
  image_url: string;
  trend_score: number;
  tags: string[];
  colors: string[];
}

interface GoogleTrend {
  keyword: string;
  current_interest: number;
  peak_interest: number;
  direction: string;
  change_pct: number;
  weekly_data: Array<{ date: string; value: number }>;
}

export default function DiscoveryPage() {
  const [trendData, setTrendData] = useState<Record<string, TrendItem[]>>({});
  const [amazonProducts, setAmazonProducts] = useState<TrendProduct[]>([]);
  const [googleTrends, setGoogleTrends] = useState<GoogleTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      fetch("/api/discovery/trends").then(r => r.ok ? r.json() : null).catch(() => null),
      fetch("/api/discovery/amazon-trending").then(r => r.ok ? r.json() : null).catch(() => null),
      fetch("/api/discovery/google-trends").then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([trends, amazon, google]) => {
      if (trends?.categories) setTrendData(trends.categories);
      if (amazon?.products) setAmazonProducts(amazon.products);
      if (google?.trends) setGoogleTrends(google.trends);
      setLoading(false);
    });
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await fetch(`/api/discovery/search?q=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const categoryIcons: Record<string, any> = {
    "Aesthetic Trends": Flame,
    "Trending Colors": Palette,
    "Trending Silhouettes": Shirt,
    "Trending Materials": Layers,
  };

  const allCategories = ["all", ...Object.keys(trendData)];

  const getDirectionBadge = (direction: string) => {
    switch (direction) {
      case "hot": return { text: "🔥 Hot", cls: "bg-red-500/20 text-red-400" };
      case "rising": return { text: "📈 Rising", cls: "bg-emerald-500/20 text-emerald-400" };
      case "declining": return { text: "📉 Declining", cls: "bg-amber-500/20 text-amber-400" };
      default: return { text: "→ Stable", cls: "bg-blue-500/20 text-blue-400" };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading trend intelligence...</p>
        </div>
      </div>
    );
  }

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
            <p className="text-muted-foreground">AI-powered fashion intelligence from multiple data sources</p>
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
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search trends... (e.g., 'quiet luxury', 'wide leg')"
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-card border border-border focus:border-primary focus:outline-none text-sm"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="mb-8 p-5 rounded-2xl bg-card border border-border">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase mb-3">
            Search Results for &quot;{searchQuery}&quot;
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {searchResults.map((result, i) => (
              <div key={i} className="p-3 rounded-xl bg-muted/50 flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{result.name}</p>
                  <p className="text-xs text-muted-foreground">{result.source} · {result.type}</p>
                </div>
                {result.score && (
                  <span className="text-sm font-bold text-primary">{result.score}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Source Badges */}
      <div className="flex flex-wrap gap-2 mb-6">
        {["Google Trends", "Amazon Best Sellers", "Fashion Blogs", "Social Media"].map(source => (
          <span key={source} className="text-xs px-3 py-1.5 rounded-full bg-muted border border-border flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            {source}
          </span>
        ))}
      </div>

      {/* Google Trends Section */}
      <div className="mb-8 p-6 rounded-2xl bg-card border border-border">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-blue-500" />
          Google Trends — Fashion Keywords
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {googleTrends.map((trend, i) => {
            const badge = getDirectionBadge(trend.direction);
            return (
              <div key={i} className="p-4 rounded-xl bg-muted/50 border border-border/50">
                <p className="font-medium text-sm mb-1 truncate">{trend.keyword}</p>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl font-bold">{trend.current_interest}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${badge.cls}`}>
                    {badge.text}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <span className={trend.change_pct >= 0 ? "text-emerald-400" : "text-red-400"}>
                    {trend.change_pct >= 0 ? "+" : ""}{trend.change_pct}%
                  </span>
                  <span>vs 3mo ago</span>
                </div>
                {/* Mini sparkline */}
                <div className="flex items-end gap-px mt-2 h-8">
                  {trend.weekly_data.map((w, wi) => (
                    <div
                      key={wi}
                      className="flex-1 rounded-t bg-primary/40 hover:bg-primary transition-colors"
                      style={{ height: `${(w.value / 100) * 100}%` }}
                      title={`${w.date}: ${w.value}`}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {allCategories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeCategory === cat
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {cat === "all" ? "All Categories" : cat}
          </button>
        ))}
      </div>

      {/* Trend Categories */}
      <div className="space-y-8 mb-10">
        {Object.entries(trendData)
          .filter(([cat]) => activeCategory === "all" || cat === activeCategory)
          .map(([categoryName, items]) => {
            const Icon = categoryIcons[categoryName] || TrendingUp;
            return (
              <div key={categoryName} className="p-6 rounded-2xl bg-card border border-border">
                <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                  <Icon className="h-5 w-5 text-primary" />
                  {categoryName}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map((item, i) => {
                    const badge = getDirectionBadge(item.direction);
                    return (
                      <div key={i} className="p-4 rounded-xl bg-muted/50 border border-border/50 hover:border-primary/30 transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {item.hex && (
                              <div
                                className="w-6 h-6 rounded-md border border-border"
                                style={{ backgroundColor: item.hex }}
                              />
                            )}
                            <h3 className="font-semibold text-sm">{item.name}</h3>
                          </div>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>
                            {badge.text}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">{item.description}</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-muted rounded-full h-2">
                            <div
                              className={`rounded-full h-2 transition-all ${
                                item.score >= 85 ? 'bg-red-500' :
                                item.score >= 75 ? 'bg-orange-500' :
                                item.score >= 65 ? 'bg-yellow-500' :
                                'bg-blue-500'
                              }`}
                              style={{ width: `${item.score}%` }}
                            />
                          </div>
                          <span className="text-sm font-bold">{item.score}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
      </div>

      {/* Amazon Best Sellers */}
      <div className="p-6 rounded-2xl bg-card border border-border">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <ShoppingBag className="h-5 w-5 text-orange-500" />
          Amazon Best Sellers — Fashion
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {amazonProducts.map((product, i) => (
            <div key={i} className="rounded-xl overflow-hidden border border-border bg-muted/30 hover:border-primary/30 transition-colors">
              <div className="aspect-square relative bg-muted">
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
                <span className="absolute top-2 left-2 text-[10px] font-bold px-1.5 py-0.5 rounded bg-orange-500/90 text-white">
                  #{product.rank}
                </span>
                <span className="absolute top-2 right-2 text-[10px] font-bold px-1.5 py-0.5 rounded bg-primary/90 text-white">
                  Score: {product.trend_score}
                </span>
              </div>
              <div className="p-3">
                <p className="text-xs font-medium line-clamp-2 mb-1.5 leading-tight">{product.name}</p>
                <p className="text-[10px] text-muted-foreground mb-1.5">{product.category}</p>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-primary font-bold">${product.price}</span>
                  <span className="text-[10px] text-muted-foreground">⭐ {product.rating} ({product.reviews.toLocaleString()})</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {product.tags.slice(0, 3).map(tag => (
                    <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
