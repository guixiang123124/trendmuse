"use client";

import { useState } from "react";
import { 
  Download, 
  Share2, 
  Heart, 
  ZoomIn,
  X,
  Clock,
  Sparkles
} from "lucide-react";
import { GenerationResult, GeneratedDesign } from "@/lib/api";

interface DesignVariantsProps {
  result: GenerationResult;
}

export default function DesignVariants({ result }: DesignVariantsProps) {
  const [selectedVariant, setSelectedVariant] = useState<GeneratedDesign | null>(null);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  const toggleFavorite = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newFavorites = new Set(favorites);
    if (newFavorites.has(id)) {
      newFavorites.delete(id);
    } else {
      newFavorites.add(id);
    }
    setFavorites(newFavorites);
  };

  const handleDownload = async (variant: GeneratedDesign, e: React.MouseEvent) => {
    e.stopPropagation();
    // In a real app, this would download the image
    window.open(variant.image_url, '_blank');
  };

  return (
    <div className="p-6 rounded-2xl bg-card border border-border">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            Generated Variations
          </h3>
          <p className="text-sm text-muted-foreground">
            {result.variations.length} variations • {result.generation_time_ms}ms
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>Style: {result.variations[0]?.style}</span>
        </div>
      </div>

      {/* Source Image */}
      <div className="mb-6">
        <p className="text-xs text-muted-foreground mb-2">Source Image</p>
        <div className="flex items-center gap-4 p-3 rounded-xl bg-muted">
          <div className="w-16 h-20 rounded-lg overflow-hidden">
            <img
              src={result.source_item.image_url}
              alt={result.source_item.name}
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <p className="font-medium">{result.source_item.name}</p>
            <p className="text-sm text-muted-foreground capitalize">{result.source_item.category}</p>
          </div>
        </div>
      </div>

      {/* Variants Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {result.variations.map((variant, index) => (
          <div
            key={variant.id}
            onClick={() => setSelectedVariant(variant)}
            className="group relative rounded-xl overflow-hidden cursor-pointer border-2 border-transparent hover:border-primary transition-all"
          >
            <div className="aspect-[3/4]">
              <img
                src={variant.image_url}
                alt={`Variation ${index + 1}`}
                className="w-full h-full object-cover transition-transform group-hover:scale-105"
              />
            </div>
            
            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="absolute bottom-0 left-0 right-0 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-white text-sm font-medium">Var. {index + 1}</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => toggleFavorite(variant.id, e)}
                      className={`p-1.5 rounded-full ${favorites.has(variant.id) ? 'bg-red-500 text-white' : 'bg-white/20 text-white'} hover:bg-red-500 transition-colors`}
                    >
                      <Heart className={`h-4 w-4 ${favorites.has(variant.id) ? 'fill-current' : ''}`} />
                    </button>
                    <button
                      onClick={(e) => handleDownload(variant, e)}
                      className="p-1.5 rounded-full bg-white/20 text-white hover:bg-primary transition-colors"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setSelectedVariant(variant)}
                      className="p-1.5 rounded-full bg-white/20 text-white hover:bg-primary transition-colors"
                    >
                      <ZoomIn className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Favorite Badge */}
            {favorites.has(variant.id) && (
              <div className="absolute top-2 right-2">
                <Heart className="h-5 w-5 fill-red-500 text-red-500" />
              </div>
            )}

            {/* Variation Number */}
            <div className="absolute top-2 left-2 px-2 py-1 rounded-full bg-black/50 text-white text-xs font-medium">
              #{index + 1}
            </div>
          </div>
        ))}
      </div>

      {/* Strength Indicator */}
      <div className="mt-4 p-3 rounded-xl bg-muted">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-muted-foreground">Variation Strength</span>
          <span className="font-medium">{(result.variations[0]?.variation_strength * 100).toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-background rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-fashion rounded-full"
            style={{ width: `${result.variations[0]?.variation_strength * 100}%` }}
          />
        </div>
      </div>

      {/* Lightbox Modal */}
      {selectedVariant && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
          <button
            onClick={() => setSelectedVariant(null)}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
          
          <div className="max-w-4xl max-h-[90vh] flex flex-col md:flex-row gap-6">
            <div className="flex-1">
              <img
                src={selectedVariant.image_url}
                alt="Design Variation"
                className="w-full h-auto max-h-[80vh] object-contain rounded-xl"
              />
            </div>
            <div className="md:w-64 p-4 bg-card rounded-xl">
              <h4 className="font-semibold mb-4">Variation Details</h4>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Style:</span>
                  <p className="font-medium capitalize">{selectedVariant.style}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Strength:</span>
                  <p className="font-medium">{(selectedVariant.variation_strength * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Prompt:</span>
                  <p className="text-xs mt-1 text-muted-foreground line-clamp-4">
                    {selectedVariant.generation_prompt}
                  </p>
                </div>
              </div>
              <div className="mt-6 flex gap-2">
                <button
                  onClick={(e) => handleDownload(selectedVariant, e)}
                  className="flex-1 px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download
                </button>
                <button
                  onClick={(e) => toggleFavorite(selectedVariant.id, e)}
                  className={`p-2 rounded-lg ${favorites.has(selectedVariant.id) ? 'bg-red-500 text-white' : 'bg-secondary'} transition-colors`}
                >
                  <Heart className={`h-5 w-5 ${favorites.has(selectedVariant.id) ? 'fill-current' : ''}`} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
