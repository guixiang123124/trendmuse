"use client";

import { useState, useEffect } from "react";
import { 
  Search, 
  Loader2, 
  TrendingUp, 
  Filter,
  BarChart3,
  RefreshCw
} from "lucide-react";
import { scanner, FashionItem, TrendAnalysis } from "@/lib/api";
import TrendCard from "@/components/TrendCard";
import ImageGallery from "@/components/ImageGallery";

export default function ScannerPage() {
  const [url, setUrl] = useState("https://www.shein.com/");
  const [items, setItems] = useState<FashionItem[]>([]);
  const [analysis, setAnalysis] = useState<TrendAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedItem, setSelectedItem] = useState<FashionItem | null>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await scanner.getCategories();
      setCategories(cats);
    } catch (e) {
      console.error("Failed to load categories:", e);
    }
  };

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await scanner.scan(url, 25, selectedCategory || undefined);
      setItems(result.items);
      
      // Load analysis
      const analysisResult = await scanner.getAnalysis();
      setAnalysis(analysisResult.data);
    } catch (e) {
      setError("Scan failed. Please try again.");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await scanner.loadDemo();
      setItems(result.items);
      
      // Load analysis
      const analysisResult = await scanner.getAnalysis();
      setAnalysis(analysisResult.data);
    } catch (e) {
      setError("Failed to load demo data.");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getTrendBadgeClass = (level: string) => {
    switch (level) {
      case "hot": return "trend-hot";
      case "rising": return "trend-rising";
      case "stable": return "trend-stable";
      case "declining": return "trend-declining";
      default: return "trend-stable";
    }
  };

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500">
            <TrendingUp className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Trend Scanner</h1>
            <p className="text-muted-foreground">Analyze fashion e-commerce sites for trending styles</p>
          </div>
        </div>
      </div>

      {/* Search Section */}
      <div className="mb-8 p-6 rounded-2xl bg-card border border-border">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter website URL (e.g., https://www.shein.com/)"
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-background border border-input focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-3 rounded-xl bg-background border border-input focus:border-primary focus:outline-none min-w-[150px]"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
            ))}
          </select>
          <button
            onClick={handleScan}
            disabled={loading || !url}
            className="px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                Scan
              </>
            )}
          </button>
          <button
            onClick={handleLoadDemo}
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-secondary text-secondary-foreground font-medium hover:bg-secondary/80 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw className="h-5 w-5" />
            Demo Data
          </button>
        </div>
        {error && (
          <p className="mt-4 text-red-500 text-sm">{error}</p>
        )}
      </div>

      {/* Analysis Summary */}
      {analysis && (
        <div className="mb-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-card border border-border">
            <p className="text-2xl font-bold">{analysis.summary.total_items}</p>
            <p className="text-sm text-muted-foreground">Items Found</p>
          </div>
          <div className="p-4 rounded-xl bg-card border border-border">
            <p className="text-2xl font-bold">{analysis.summary.avg_trend_score.toFixed(1)}</p>
            <p className="text-sm text-muted-foreground">Avg Trend Score</p>
          </div>
          <div className="p-4 rounded-xl bg-card border border-border">
            <p className="text-2xl font-bold">${analysis.summary.avg_price.toFixed(0)}</p>
            <p className="text-sm text-muted-foreground">Avg Price</p>
          </div>
          <div className="p-4 rounded-xl bg-card border border-border">
            <p className="text-2xl font-bold">{(analysis.summary.total_sales / 1000).toFixed(1)}k</p>
            <p className="text-sm text-muted-foreground">Total Sales</p>
          </div>
        </div>
      )}

      {/* Trend Analysis Charts */}
      {analysis && (
        <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Categories */}
          <div className="p-6 rounded-2xl bg-card border border-border">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-pink-500" />
              Top Categories
            </h3>
            <div className="space-y-3">
              {analysis.top_categories.slice(0, 5).map((cat) => (
                <div key={cat.category} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium capitalize">{cat.category}</span>
                      <span className="text-sm text-muted-foreground">{cat.count} items</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-fashion rounded-full"
                        style={{ width: `${cat.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trending Colors */}
          <div className="p-6 rounded-2xl bg-card border border-border">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Filter className="h-5 w-5 text-purple-500" />
              Trending Colors
            </h3>
            <div className="flex flex-wrap gap-2">
              {analysis.trending_colors.slice(0, 10).map((color) => (
                <div 
                  key={color.color}
                  className="px-3 py-2 rounded-lg bg-muted text-sm"
                >
                  <span className="font-medium">{color.color}</span>
                  <span className="text-muted-foreground ml-2">({color.count})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Results Grid */}
      {items.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Scanned Items ({items.length})</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {items.map((item) => (
              <TrendCard 
                key={item.id} 
                item={item} 
                onSelect={() => setSelectedItem(item)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {items.length === 0 && !loading && (
        <div className="text-center py-16">
          <div className="inline-flex p-4 rounded-full bg-muted mb-4">
            <TrendingUp className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No items scanned yet</h3>
          <p className="text-muted-foreground mb-6">
            Enter a URL or load demo data to start scanning
          </p>
          <button
            onClick={handleLoadDemo}
            className="px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
          >
            Load Demo Data
          </button>
        </div>
      )}

      {/* Selected Item Modal */}
      {selectedItem && (
        <ImageGallery 
          item={selectedItem} 
          onClose={() => setSelectedItem(null)} 
        />
      )}
    </div>
  );
}
