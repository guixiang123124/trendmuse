"use client";

import { useState } from "react";
import { 
  Download, 
  ZoomIn, 
  X, 
  ArrowRight,
  Clock,
  PenTool,
  Layers
} from "lucide-react";
import { ConversionResult } from "@/lib/api";

interface SketchPreviewProps {
  result: ConversionResult;
}

export default function SketchPreview({ result }: SketchPreviewProps) {
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  const handleDownload = () => {
    // In production, this would download the actual sketch file
    window.open(result.sketch.image_url, '_blank');
  };

  return (
    <div className="p-6 rounded-2xl bg-card border border-border">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <PenTool className="h-5 w-5 text-blue-500" />
            Sketch Result
          </h3>
          <p className="text-sm text-muted-foreground">
            Converted in {result.conversion_time_ms}ms
          </p>
        </div>
        <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-sm capitalize">
          {result.sketch.style.replace('_', ' ')}
        </span>
      </div>

      {/* Sketch Image */}
      <div 
        className="relative rounded-xl overflow-hidden bg-white cursor-pointer group"
        onClick={() => setShowFullscreen(true)}
      >
        <img
          src={result.sketch.image_url}
          alt="Converted Sketch"
          className="w-full h-auto"
          onError={(e) => {
            // Fallback if sketch image fails to load
            (e.target as HTMLImageElement).src = result.source_item.image_url;
          }}
        />
        
        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
          <button className="p-3 rounded-full bg-white/20 text-white hover:bg-white/30 transition-colors">
            <ZoomIn className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* Details */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-muted">
          <p className="text-xs text-muted-foreground">Detail Level</p>
          <p className="text-sm font-medium">{(result.sketch.detail_level * 100).toFixed(0)}%</p>
        </div>
        <div className="p-3 rounded-xl bg-muted">
          <p className="text-xs text-muted-foreground">Style</p>
          <p className="text-sm font-medium capitalize">{result.sketch.style.replace('_', ' ')}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={handleDownload}
          className="flex-1 px-4 py-2 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
        >
          <Download className="h-4 w-4" />
          Download Sketch
        </button>
        <button
          onClick={() => setShowComparison(true)}
          className="px-4 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
        >
          <Layers className="h-4 w-4" />
        </button>
      </div>

      {/* Fullscreen Modal */}
      {showFullscreen && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
          <button
            onClick={() => setShowFullscreen(false)}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
          <img
            src={result.sketch.image_url}
            alt="Sketch Fullscreen"
            className="max-w-full max-h-[90vh] object-contain rounded-xl"
            onError={(e) => {
              (e.target as HTMLImageElement).src = result.source_item.image_url;
            }}
          />
        </div>
      )}

      {/* Comparison Modal */}
      {showComparison && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
          <button
            onClick={() => setShowComparison(false)}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
          
          <div className="flex items-center gap-4">
            <div className="text-center">
              <img
                src={result.source_item.image_url}
                alt="Original"
                className="max-h-[70vh] rounded-xl"
              />
              <p className="mt-2 text-white font-medium">Original</p>
            </div>
            
            <ArrowRight className="h-8 w-8 text-white" />
            
            <div className="text-center">
              <img
                src={result.sketch.image_url}
                alt="Sketch"
                className="max-h-[70vh] rounded-xl bg-white"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = result.source_item.image_url;
                }}
              />
              <p className="mt-2 text-white font-medium">Sketch</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
