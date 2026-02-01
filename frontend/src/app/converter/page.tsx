"use client";

import { useState, useEffect } from "react";
import { 
  PenTool, 
  Loader2, 
  Wand2,
  Sliders,
  RefreshCw,
  Download,
  ArrowRight
} from "lucide-react";
import { scanner, converter, FashionItem, ConversionResult } from "@/lib/api";
import SketchPreview from "@/components/SketchPreview";

interface SketchStyle {
  id: string;
  name: string;
  description: string;
}

export default function ConverterPage() {
  const [items, setItems] = useState<FashionItem[]>([]);
  const [styles, setStyles] = useState<SketchStyle[]>([]);
  const [selectedItem, setSelectedItem] = useState<FashionItem | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string>("technical");
  const [detailLevel, setDetailLevel] = useState(0.5);
  const [lineThickness, setLineThickness] = useState(1.0);
  const [converting, setConverting] = useState(false);
  const [conversionResult, setConversionResult] = useState<ConversionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [itemsData, stylesData] = await Promise.all([
        scanner.getItems({ limit: 20 }),
        converter.getStyles(),
      ]);
      setItems(itemsData);
      setStyles(stylesData);

      if (itemsData.length === 0) {
        await scanner.loadDemo();
        const newItems = await scanner.getItems({ limit: 20 });
        setItems(newItems);
      }
    } catch (e) {
      console.error("Failed to load data:", e);
    }
  };

  const handleConvert = async () => {
    if (!selectedItem) return;

    setConverting(true);
    setError(null);
    try {
      const result = await converter.convert(selectedItem.id, {
        style: selectedStyle,
        detailLevel,
        lineThickness,
      });
      setConversionResult(result);
    } catch (e) {
      setError("Conversion failed. Please try again.");
      console.error(e);
    } finally {
      setConverting(false);
    }
  };

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500">
            <PenTool className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Sketch Converter</h1>
            <p className="text-muted-foreground">Transform photos into fashion sketches</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Source Selection */}
        <div>
          <div className="p-6 rounded-2xl bg-card border border-border">
            <h2 className="text-lg font-semibold mb-4">Select Image</h2>
            
            {items.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No items available.</p>
                <button
                  onClick={loadData}
                  className="px-4 py-2 rounded-lg bg-primary text-primary-foreground"
                >
                  <RefreshCw className="h-4 w-4 inline mr-2" />
                  Load Demo Data
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 max-h-[600px] overflow-y-auto pr-2">
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
                    <div className="aspect-square">
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Middle: Preview */}
        <div>
          {selectedItem ? (
            <div className="p-6 rounded-2xl bg-card border border-border h-full">
              <h3 className="text-lg font-semibold mb-4">Original</h3>
              <div className="aspect-[3/4] rounded-xl overflow-hidden mb-4 bg-muted">
                <img
                  src={selectedItem.image_url}
                  alt={selectedItem.name}
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="font-medium">{selectedItem.name}</p>
              <p className="text-sm text-muted-foreground capitalize">{selectedItem.category} • {selectedItem.brand}</p>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-card border border-border h-full flex items-center justify-center">
              <div className="text-center">
                <div className="inline-flex p-4 rounded-full bg-muted mb-4">
                  <PenTool className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">Select an image to convert</p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Controls & Result */}
        <div className="space-y-6">
          {/* Conversion Settings */}
          <div className="p-6 rounded-2xl bg-card border border-border">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
              <Sliders className="h-4 w-4" />
              Sketch Settings
            </h3>

            {/* Style Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Sketch Style</label>
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

            {/* Detail Level */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Detail Level: {(detailLevel * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={detailLevel}
                onChange={(e) => setDetailLevel(parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Minimal</span>
                <span>Detailed</span>
              </div>
            </div>

            {/* Line Thickness */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Line Thickness: {lineThickness.toFixed(1)}x
              </label>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.5"
                value={lineThickness}
                onChange={(e) => setLineThickness(parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
            </div>

            {/* Convert Button */}
            <button
              onClick={handleConvert}
              disabled={!selectedItem || converting}
              className="w-full px-6 py-4 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {converting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Converting...
                </>
              ) : (
                <>
                  <PenTool className="h-5 w-5" />
                  Convert to Sketch
                </>
              )}
            </button>

            {error && (
              <p className="mt-4 text-red-500 text-sm text-center">{error}</p>
            )}
          </div>

          {/* Conversion Result */}
          {conversionResult && (
            <SketchPreview result={conversionResult} />
          )}

          {/* Demo Notice */}
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <p className="text-xs text-blue-400">
              <strong>Demo Mode:</strong> Using edge detection. Add ControlNet integration for higher quality sketches.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
