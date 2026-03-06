"use client";

import { useState } from "react";
import { X, Sparkles, Download, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

const API_BASE = "https://api.trendmuse.app";

interface TrendSignal {
  id?: string | number;
  title: string;
  image_url?: string;
  brand?: string;
  category?: string;
}

interface GeneratedImage {
  url: string;
  prompt_used: string;
}

interface Props {
  signal: TrendSignal;
  onClose: () => void;
}

export default function GenerateDesignModal({ signal, onClose }: Props) {
  const [style, setStyle] = useState<"variation" | "inspired" | "remix">("variation");
  const [model, setModel] = useState<"nano-banana" | "seedream-4.5">("nano-banana");
  const [count, setCount] = useState(1);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<GeneratedImage[]>([]);
  const [error, setError] = useState("");
  const [expandedPrompt, setExpandedPrompt] = useState<number | null>(null);

  const getToken = () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("token") || "";
    }
    return "";
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setResults([]);

    try {
      const token = getToken();
      if (!token) {
        setError("Please log in to generate designs");
        setLoading(false);
        return;
      }

      const res = await fetch(`${API_BASE}/api/generator/generate/from-trend`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          signal_id: signal.id,
          style,
          model,
          count,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Error ${res.status}`);
      }

      const data = await res.json();
      setResults(data.images || []);
    } catch (e: any) {
      setError(e.message || "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = async (url: string, index: number) => {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `design-${signal.title?.slice(0, 20)}-${index + 1}.png`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      window.open(url, "_blank");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-card rounded-2xl border border-border w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Generate Design</h2>
              <p className="text-xs text-muted-foreground line-clamp-1">{signal.title}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-muted transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Reference product */}
        <div className="p-5 border-b border-border">
          <div className="flex gap-4">
            {signal.image_url && (
              <img
                src={signal.image_url}
                alt={signal.title}
                className="w-24 h-24 object-cover rounded-xl border border-border"
              />
            )}
            <div className="flex-1">
              <p className="text-sm font-medium mb-1">{signal.title}</p>
              {signal.brand && <p className="text-xs text-muted-foreground">{signal.brand}</p>}
              {signal.category && (
                <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground capitalize">
                  {signal.category}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Options */}
        <div className="p-5 space-y-4">
          {/* Style */}
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 block">
              Style
            </label>
            <div className="flex gap-2">
              {(["variation", "inspired", "remix"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setStyle(s)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                    style === s
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Model */}
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 block">
              Model
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setModel("nano-banana")}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  model === "nano-banana"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                ⚡ Fast (1 credit)
              </button>
              <button
                onClick={() => setModel("seedream-4.5")}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  model === "seedream-4.5"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                💎 Premium (3 credits)
              </button>
            </div>
          </div>

          {/* Count */}
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 block">
              Count: {count}
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((n) => (
                <button
                  key={n}
                  onClick={() => setCount(n)}
                  className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                    count === n
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white font-semibold text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate ({count * (model === "nano-banana" ? 1 : 3)} credits)
              </>
            )}
          </button>

          {error && (
            <p className="text-sm text-red-500 text-center">{error}</p>
          )}
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="p-5 border-t border-border">
            <h3 className="text-sm font-semibold mb-3">Generated Designs</h3>
            <div className="grid grid-cols-2 gap-3">
              {results.map((img, i) => (
                <div key={i} className="relative group">
                  <img
                    src={img.url}
                    alt={`Design ${i + 1}`}
                    className="w-full aspect-square object-cover rounded-xl border border-border"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 rounded-xl transition-colors flex items-end justify-between p-2 opacity-0 group-hover:opacity-100">
                    <button
                      onClick={() => setExpandedPrompt(expandedPrompt === i ? null : i)}
                      className="text-[10px] text-white bg-black/50 rounded px-2 py-1"
                    >
                      {expandedPrompt === i ? <ChevronUp className="h-3 w-3" /> : "Prompt"}
                    </button>
                    <button
                      onClick={() => downloadImage(img.url, i)}
                      className="p-1.5 rounded-lg bg-white/90 text-black hover:bg-white transition-colors"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  </div>
                  {expandedPrompt === i && (
                    <div className="mt-1 p-2 bg-muted rounded-lg text-[10px] text-muted-foreground line-clamp-4">
                      {img.prompt_used}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
