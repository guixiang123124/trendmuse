"use client";

import { useState } from "react";
import { 
  X, 
  TrendingUp, 
  Star, 
  ShoppingBag, 
  ExternalLink,
  Sparkles,
  PenTool,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { FashionItem } from "@/lib/api";
import Link from "next/link";

interface ImageGalleryProps {
  item: FashionItem;
  onClose: () => void;
}

export default function ImageGallery({ item, onClose }: ImageGalleryProps) {
  const getTrendBadgeClass = (level: string) => {
    switch (level) {
      case "hot": return "bg-red-500/20 text-red-400 border-red-500/30";
      case "rising": return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      case "stable": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "declining": return "bg-gray-500/20 text-gray-400 border-gray-500/30";
      default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col md:flex-row">
        {/* Image Section */}
        <div className="md:w-1/2 relative">
          <img
            src={item.image_url}
            alt={item.name}
            className="w-full h-full object-cover min-h-[300px] md:min-h-full"
          />
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>

          {/* Trend Badge */}
          <div className={`absolute top-4 left-4 px-3 py-1.5 rounded-full border backdrop-blur-sm ${getTrendBadgeClass(item.trend_level)}`}>
            <span className="text-sm font-medium capitalize">{item.trend_level}</span>
          </div>
        </div>

        {/* Details Section */}
        <div className="md:w-1/2 p-6 overflow-y-auto">
          {/* Brand & Category */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-primary">{item.brand}</span>
            <span className="text-sm text-muted-foreground capitalize">{item.category}</span>
          </div>

          {/* Name */}
          <h2 className="text-2xl font-bold mb-4">{item.name}</h2>

          {/* Price */}
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl font-bold">${item.price.toFixed(2)}</span>
            {item.original_price && item.original_price > item.price && (
              <>
                <span className="text-lg text-muted-foreground line-through">${item.original_price.toFixed(2)}</span>
                <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 text-sm font-medium">
                  -{Math.round((1 - item.price / item.original_price) * 100)}%
                </span>
              </>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-3 rounded-xl bg-muted text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <TrendingUp className="h-4 w-4 text-primary" />
              </div>
              <p className="text-lg font-bold">{item.trend_score.toFixed(0)}</p>
              <p className="text-xs text-muted-foreground">Trend Score</p>
            </div>
            <div className="p-3 rounded-xl bg-muted text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
              </div>
              <p className="text-lg font-bold">{item.rating.toFixed(1)}</p>
              <p className="text-xs text-muted-foreground">{item.reviews_count} reviews</p>
            </div>
            <div className="p-3 rounded-xl bg-muted text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <ShoppingBag className="h-4 w-4 text-green-500" />
              </div>
              <p className="text-lg font-bold">{item.sales_count > 1000 ? `${(item.sales_count / 1000).toFixed(1)}k` : item.sales_count}</p>
              <p className="text-xs text-muted-foreground">Sold</p>
            </div>
          </div>

          {/* Colors */}
          {item.colors.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium mb-2">Colors</h4>
              <div className="flex flex-wrap gap-2">
                {item.colors.map((color) => (
                  <span
                    key={color}
                    className="px-3 py-1.5 rounded-lg bg-muted text-sm"
                  >
                    {color}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {item.tags.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium mb-2">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-3">
            <Link
              href={`/generator?item=${item.id}`}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-fashion text-white font-medium hover:opacity-90 transition-opacity"
            >
              <Sparkles className="h-5 w-5" />
              Generate Variations
            </Link>
            <Link
              href={`/converter?item=${item.id}`}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 text-white font-medium hover:opacity-90 transition-opacity"
            >
              <PenTool className="h-5 w-5" />
              Convert to Sketch
            </Link>
            <a
              href={item.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-secondary text-secondary-foreground font-medium hover:bg-secondary/80 transition-colors"
            >
              <ExternalLink className="h-5 w-5" />
              View Original
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
