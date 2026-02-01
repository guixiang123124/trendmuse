"use client";

import { useState } from "react";
import { 
  TrendingUp, 
  Star, 
  ShoppingBag, 
  Flame, 
  ArrowUp, 
  Minus, 
  ArrowDown,
  Sparkles,
  PenTool,
  ExternalLink
} from "lucide-react";
import { FashionItem } from "@/lib/api";
import Link from "next/link";

interface TrendCardProps {
  item: FashionItem;
  onSelect?: () => void;
}

export default function TrendCard({ item, onSelect }: TrendCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);

  const getTrendIcon = (level: string) => {
    switch (level) {
      case "hot": return <Flame className="h-3 w-3" />;
      case "rising": return <ArrowUp className="h-3 w-3" />;
      case "stable": return <Minus className="h-3 w-3" />;
      case "declining": return <ArrowDown className="h-3 w-3" />;
      default: return <Minus className="h-3 w-3" />;
    }
  };

  const getTrendBadgeClass = (level: string) => {
    switch (level) {
      case "hot": return "bg-red-500/20 text-red-400 border-red-500/30";
      case "rising": return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      case "stable": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "declining": return "bg-gray-500/20 text-gray-400 border-gray-500/30";
      default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const formatPrice = (price: number, originalPrice?: number) => {
    if (originalPrice && originalPrice > price) {
      const discount = Math.round((1 - price / originalPrice) * 100);
      return (
        <div className="flex items-center gap-2">
          <span className="font-bold">${price.toFixed(2)}</span>
          <span className="text-muted-foreground line-through text-sm">${originalPrice.toFixed(2)}</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">-{discount}%</span>
        </div>
      );
    }
    return <span className="font-bold">${price.toFixed(2)}</span>;
  };

  return (
    <div className="group rounded-2xl bg-card border border-border overflow-hidden card-hover">
      {/* Image */}
      <div className="aspect-[3/4] relative overflow-hidden bg-muted">
        {!imageLoaded && (
          <div className="absolute inset-0 shimmer bg-muted" />
        )}
        <img
          src={item.image_url}
          alt={item.name}
          className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={() => setImageLoaded(true)}
        />
        
        {/* Trend Badge */}
        <div className={`absolute top-3 left-3 px-2 py-1 rounded-full border text-xs font-medium flex items-center gap-1 ${getTrendBadgeClass(item.trend_level)}`}>
          {getTrendIcon(item.trend_level)}
          <span className="capitalize">{item.trend_level}</span>
        </div>

        {/* Trend Score */}
        <div className="absolute top-3 right-3 px-2 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-bold flex items-center gap-1">
          <TrendingUp className="h-3 w-3" />
          {item.trend_score.toFixed(0)}
        </div>

        {/* Quick Actions Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-4 gap-2">
          <Link
            href={`/generator?item=${item.id}`}
            className="p-2 rounded-full bg-purple-500 text-white hover:bg-purple-600 transition-colors"
            title="Generate Variations"
          >
            <Sparkles className="h-4 w-4" />
          </Link>
          <Link
            href={`/converter?item=${item.id}`}
            className="p-2 rounded-full bg-blue-500 text-white hover:bg-blue-600 transition-colors"
            title="Convert to Sketch"
          >
            <PenTool className="h-4 w-4" />
          </Link>
          <a
            href={item.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-full bg-gray-500 text-white hover:bg-gray-600 transition-colors"
            title="View Product"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="p-4" onClick={onSelect}>
        {/* Brand & Category */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-primary">{item.brand}</span>
          <span className="text-xs text-muted-foreground capitalize">{item.category}</span>
        </div>

        {/* Name */}
        <h3 className="font-medium mb-2 line-clamp-2 group-hover:text-primary transition-colors cursor-pointer">
          {item.name}
        </h3>

        {/* Price */}
        <div className="mb-3">
          {formatPrice(item.price, item.original_price ?? undefined)}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
            <span>{item.rating.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-1">
            <ShoppingBag className="h-3 w-3" />
            <span>{item.sales_count > 1000 ? `${(item.sales_count / 1000).toFixed(1)}k` : item.sales_count} sold</span>
          </div>
        </div>

        {/* Colors */}
        {item.colors.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {item.colors.slice(0, 3).map((color) => (
              <span
                key={color}
                className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground"
              >
                {color}
              </span>
            ))}
            {item.colors.length > 3 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                +{item.colors.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Tags */}
        {item.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {item.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
