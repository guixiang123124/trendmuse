"use client";

import { useState, useEffect } from "react";
import { 
  Sparkles, 
  Loader2, 
  Wand2,
  Palette,
  Sliders,
  RefreshCw
} from "lucide-react";
import { scanner, generator, FashionItem, GeneratedDesign, GenerationResult } from "@/lib/api";
import TrendCard from "@/components/TrendCard";
import DesignVariants from "@/components/DesignVariants";

interface GenerationStyle {
  id: string;
  name: string;
  description: string;
}

export default function GeneratorPage() {
  const [items, setItems] = useState<FashionItem[]>([]);
  const [styles, setStyles] = useState<GenerationStyle[]>([]);
  const [selectedItem, setSelectedItem] = useState<FashionItem | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string>("minimalist");
  const [variationStrength, setVariationStrength] = useState(0.5);
  const [numVariations, setNumVariations] = useState(4);
  const [generating, setGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Try to load from database first
      const dbRes = await fetch("/api/generator/items-from-db?limit=30");
      if (dbRes.ok) {
        const dbItems = await dbRes.json();
        if (dbItems.length > 0) {
          // Convert to FashionItem format
          const fashionItems = dbItems.map((item: any) => ({
            id: item.id,
            name: item.name,
            price: item.price || 0,
            currency: "USD",
            image_url: item.image_url,
            product_url: item.product_url || "",
            category: item.category || "other",
            brand: item.brand || item.source || "",
            reviews_count: 0,
            rating: 0,
            sales_count: 0,
            trend_score: 50,
            trend_level: "stable",
            colors: [],
            tags: []
          }));
          setItems(fashionItems);
        }
      }
      
      // Load styles
      const stylesData = await generator.getStyles();
      setStyles(stylesData);
    } catch (e) {
      console.error("Failed to load data:", e);
      // Fallback to old method
      try {
        const [itemsData, stylesData] = await Promise.all([
          scanner.getItems({ limit: 20 }),
          generator.getStyles(),
        ]);
        setItems(itemsData);
        setStyles(stylesData);
      } catch (e2) {
        console.error("Fallback also failed:", e2);
      }
    }
  };

  const handleGenerate = async () => {
    if (!selectedItem) return;

    setGenerating(true);
    setError(null);
    try {
      const result = await generator.generate(selectedItem.id, {
        style: selectedStyle,
        variationStrength,
        numVariations,
      });
      setGenerationResult(result);
    } catch (e) {
      setError("Generation failed. Please try again.");
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-violet-500">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Design Generator</h1>
            <p className="text-muted-foreground">Create AI-powered design variations</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Source Selection */}
        <div className="lg:col-span-2">
          <div className="mb-6 p-6 rounded-2xl bg-card border border-border">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Palette className="h-5 w-5 text-purple-500" />
              Select Source Image
            </h2>
            
            {items.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No items available. Load some first.</p>
                <button
                  onClick={loadData}
                  className="px-4 py-2 rounded-lg bg-primary text-primary-foreground"
                >
                  <RefreshCw className="h-4 w-4 inline mr-2" />
                  Load Demo Data
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 max-h-[500px] overflow-y-auto pr-2">
                {items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className={`
                      cursor-pointer rounded-xl overflow-hidden border-2 transition-all
                      ${selectedItem?.id === item.id 
                        ? "border-primary ring-2 ring-primary/20" 
                        : "border-transparent hover:border-primary/50"
                      }
                    `}
                  >
                    <div className="aspect-[3/4] relative">
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-full h-full object-cover"
                      />
                      {selectedItem?.id === item.id && (
                        <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                          <div className="p-2 rounded-full bg-primary">
                            <Sparkles className="h-5 w-5 text-white" />
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="p-2 bg-muted">
                      <p className="text-xs font-medium truncate">{item.name}</p>
                      <p className="text-xs text-muted-foreground">${item.price}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Generation Results */}
          {generationResult && (
            <DesignVariants result={generationResult} />
          )}
        </div>

        {/* Right: Controls */}
        <div className="space-y-6">
          {/* Selected Item Preview */}
          {selectedItem && (
            <div className="p-6 rounded-2xl bg-card border border-border">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                Selected
              </h3>
              <div className="aspect-[3/4] rounded-xl overflow-hidden mb-4">
                <img
                  src={selectedItem.image_url}
                  alt={selectedItem.name}
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="font-medium">{selectedItem.name}</p>
              <p className="text-sm text-muted-foreground capitalize">{selectedItem.category}</p>
            </div>
          )}

          {/* Generation Settings */}
          <div className="p-6 rounded-2xl bg-card border border-border">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
              <Sliders className="h-4 w-4" />
              Generation Settings
            </h3>

            {/* Style Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Style</label>
              <select
                value={selectedStyle}
                onChange={(e) => setSelectedStyle(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-background border border-input focus:border-primary focus:outline-none"
              >
                {styles.map((style) => (
                  <option key={style.id} value={style.id}>
                    {style.name}
                  </option>
                ))}
              </select>
              {styles.find(s => s.id === selectedStyle) && (
                <p className="text-xs text-muted-foreground mt-2">
                  {styles.find(s => s.id === selectedStyle)?.description}
                </p>
              )}
            </div>

            {/* Variation Strength */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Variation Strength: {(variationStrength * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={variationStrength}
                onChange={(e) => setVariationStrength(parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Subtle</span>
                <span>Dramatic</span>
              </div>
            </div>

            {/* Number of Variations */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Variations: {numVariations}
              </label>
              <input
                type="range"
                min="1"
                max="8"
                step="1"
                value={numVariations}
                onChange={(e) => setNumVariations(parseInt(e.target.value))}
                className="w-full accent-primary"
              />
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={!selectedItem || generating}
              className="w-full px-6 py-4 rounded-xl bg-gradient-fashion text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {generating ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Wand2 className="h-5 w-5" />
                  Generate Variations
                </>
              )}
            </button>

            {error && (
              <p className="mt-4 text-red-500 text-sm text-center">{error}</p>
            )}
          </div>

          {/* Demo Notice */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <p className="text-xs text-amber-500">
              <strong>Demo Mode:</strong> Using placeholder images. Add Replicate API key for real AI generation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
