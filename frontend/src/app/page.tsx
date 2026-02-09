"use client";

import { useState, useEffect } from "react";
import { 
  TrendingUp, 
  Sparkles, 
  PenTool, 
  ArrowRight,
  Zap,
  BarChart3,
  Flame,
  Eye,
  Globe,
  Palette,
  Search
} from "lucide-react";
import Link from "next/link";

interface DashboardData {
  summary: {
    total_trends_tracked: number;
    hot_trends: number;
    rising_trends: number;
    data_sources: string[];
  };
  hot_trends: Array<{
    name: string;
    score: number;
    direction: string;
    description?: string;
    source_category: string;
  }>;
  trending_products: Array<{
    rank: number;
    name: string;
    price: number;
    rating: number;
    reviews: number;
    image_url: string;
    trend_score: number;
    tags: string[];
    colors: string[];
    category: string;
  }>;
  color_palette: Array<{
    name: string;
    score: number;
    direction: string;
    hex?: string;
    description?: string;
  }>;
}

interface DbStats {
  overview?: {
    total_products: number;
    total_sources: number;
    total_categories: number;
  };
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [dbStats, setDbStats] = useState<DbStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/discovery/dashboard").then(r => r.ok ? r.json() : null).catch(() => null),
      fetch("/api/trends/summary").then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([dash, stats]) => {
      setDashboard(dash);
      setDbStats(stats);
      setLoading(false);
    });
  }, []);

  const features = [
    {
      title: "Trend Discovery",
      description: "AI-powered trend intelligence from Google Trends, Amazon, and fashion data sources",
      icon: Globe,
      href: "/discovery",
      gradient: "from-emerald-500 to-teal-500",
      badge: "NEW",
    },
    {
      title: "Trending Products",
      description: "Browse scraped products by brand and generate AI design variations",
      icon: Flame,
      href: "/trending",
      gradient: "from-orange-500 to-red-500",
    },
    {
      title: "Design Generator",
      description: "Create AI-powered design variations using GrsAI Nano Banana",
      icon: Sparkles,
      href: "/generator",
      gradient: "from-purple-500 to-violet-500",
    },
    {
      title: "Trend Scanner",
      description: "Scrape fashion e-commerce sites to build your product database",
      icon: Search,
      href: "/scanner",
      gradient: "from-pink-500 to-rose-500",
    },
  ];

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 rounded-xl bg-gradient-fashion">
            <Zap className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold gradient-text">TrendMuse 2.0</h1>
            <p className="text-muted-foreground">AI-Powered Fashion Intelligence Platform</p>
          </div>
        </div>
        <p className="text-lg text-muted-foreground max-w-2xl">
          Discover what&apos;s trending, generate designs informed by real market data, and stay ahead of the fashion curve.
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/20">
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{dashboard?.summary?.total_trends_tracked || 0}</p>
              <p className="text-xs text-muted-foreground">Trends Tracked</p>
            </div>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-red-500/20">
              <Flame className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{dashboard?.summary?.hot_trends || 0}</p>
              <p className="text-xs text-muted-foreground">Hot Right Now</p>
            </div>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/20">
              <BarChart3 className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{dbStats?.overview?.total_products?.toLocaleString() || 0}</p>
              <p className="text-xs text-muted-foreground">Products Scraped</p>
            </div>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/20">
              <Globe className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{dashboard?.summary?.data_sources?.length || 4}</p>
              <p className="text-xs text-muted-foreground">Data Sources</p>
            </div>
          </div>
        </div>
      </div>

      {/* Hot Trends + Color Palette */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
        {/* Hot Trends */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Flame className="h-5 w-5 text-orange-500" />
              Hot Trends Right Now
            </h2>
            <Link href="/discovery" className="text-sm text-primary hover:underline flex items-center gap-1">
              View All <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {(dashboard?.hot_trends || []).slice(0, 6).map((trend, i) => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-muted/50 hover:bg-muted transition-colors">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center">
                  <span className="text-sm font-bold text-orange-500">#{i + 1}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{trend.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{trend.description}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    trend.direction === 'hot' ? 'bg-red-500/20 text-red-400' :
                    trend.direction === 'rising' ? 'bg-emerald-500/20 text-emerald-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {trend.direction === 'hot' ? '🔥 Hot' : trend.direction === 'rising' ? '📈 Rising' : '→ Stable'}
                  </span>
                  <span className="text-sm font-bold text-primary">{trend.score}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Color Palette */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Palette className="h-5 w-5 text-purple-500" />
            Trending Colors
          </h2>
          <div className="space-y-3">
            {(dashboard?.color_palette || []).map((color, i) => (
              <div key={i} className="flex items-center gap-3">
                <div 
                  className="w-8 h-8 rounded-lg border border-border flex-shrink-0"
                  style={{ backgroundColor: color.hex || '#888' }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{color.name}</p>
                  <div className="w-full bg-muted rounded-full h-1.5 mt-1">
                    <div 
                      className="bg-primary rounded-full h-1.5 transition-all"
                      style={{ width: `${color.score}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">{color.score}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
        {features.map((feature) => (
          <Link
            key={feature.title}
            href={feature.href}
            className="group p-5 rounded-2xl bg-card border border-border card-hover relative"
          >
            {feature.badge && (
              <span className="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {feature.badge}
              </span>
            )}
            <div className={`inline-flex p-2.5 rounded-xl bg-gradient-to-br ${feature.gradient} mb-3`}>
              <feature.icon className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-base font-semibold mb-1 group-hover:text-primary transition-colors">
              {feature.title}
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              {feature.description}
            </p>
            <div className="flex items-center text-primary gap-1.5">
              <span className="text-xs font-medium">Explore</span>
              <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
            </div>
          </Link>
        ))}
      </div>

      {/* Trending Products Preview */}
      {dashboard?.trending_products && dashboard.trending_products.length > 0 && (
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-500" />
              Top Trending Products
            </h2>
            <Link href="/discovery" className="text-sm text-primary hover:underline flex items-center gap-1">
              See More <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {dashboard.trending_products.slice(0, 6).map((product, i) => (
              <div key={i} className="rounded-xl overflow-hidden border border-border bg-muted/30">
                <div className="aspect-square relative bg-muted">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                  <span className="absolute top-2 left-2 text-[10px] font-bold px-1.5 py-0.5 rounded bg-primary/90 text-white">
                    #{product.rank}
                  </span>
                </div>
                <div className="p-2.5">
                  <p className="text-xs font-medium truncate">{product.name}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-primary font-bold">${product.price}</span>
                    <span className="text-[10px] text-muted-foreground">⭐ {product.rating}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
