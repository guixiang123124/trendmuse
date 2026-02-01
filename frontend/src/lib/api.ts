/**
 * TrendMuse API Client
 */

const API_BASE = "/api";

// Types
export interface FashionItem {
  id: string;
  name: string;
  price: number;
  currency: string;
  original_price?: number;
  image_url: string;
  local_image_path?: string;
  product_url: string;
  category: string;
  brand: string;
  reviews_count: number;
  rating: number;
  sales_count: number;
  trend_score: number;
  trend_level: "hot" | "rising" | "stable" | "declining";
  colors: string[];
  tags: string[];
  scraped_at: string;
}

export interface ScanResult {
  source_url: string;
  items: FashionItem[];
  total_found: number;
  scan_duration_ms: number;
  timestamp: string;
}

export interface GeneratedDesign {
  id: string;
  source_item_id: string;
  image_url: string;
  local_image_path?: string;
  style: string;
  variation_strength: number;
  generation_prompt: string;
  created_at: string;
}

export interface GenerationResult {
  source_item: FashionItem;
  variations: GeneratedDesign[];
  generation_time_ms: number;
}

export interface ConvertedSketch {
  id: string;
  source_item_id: string;
  image_url: string;
  local_image_path?: string;
  style: string;
  detail_level: number;
  created_at: string;
}

export interface ConversionResult {
  source_item: FashionItem;
  sketch: ConvertedSketch;
  conversion_time_ms: number;
}

export interface TrendAnalysis {
  summary: {
    total_items: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    avg_trend_score: number;
    total_reviews: number;
    total_sales: number;
  };
  top_categories: Array<{
    category: string;
    count: number;
    percentage: number;
    avg_trend_score: number;
  }>;
  trending_colors: Array<{
    color: string;
    count: number;
    avg_trend_score: number;
  }>;
  popular_tags: Array<{
    tag: string;
    count: number;
    avg_trend_score: number;
  }>;
  hot_items: Array<{
    id: string;
    name: string;
    trend_score: number;
    price: number;
    category: string;
  }>;
}

// API Functions

/**
 * Scanner API
 */
export const scanner = {
  async scan(url: string, maxItems = 20, categoryFilter?: string): Promise<ScanResult> {
    const response = await fetch(`${API_BASE}/scanner/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        max_items: maxItems,
        category_filter: categoryFilter,
      }),
    });
    if (!response.ok) throw new Error("Scan failed");
    return response.json();
  },

  async loadDemo(): Promise<ScanResult> {
    const response = await fetch(`${API_BASE}/scanner/demo`, { method: "POST" });
    if (!response.ok) throw new Error("Failed to load demo data");
    return response.json();
  },

  async getItems(options?: {
    category?: string;
    minTrendScore?: number;
    sortBy?: string;
    limit?: number;
  }): Promise<FashionItem[]> {
    const params = new URLSearchParams();
    if (options?.category) params.set("category", options.category);
    if (options?.minTrendScore) params.set("min_trend_score", String(options.minTrendScore));
    if (options?.sortBy) params.set("sort_by", options.sortBy);
    if (options?.limit) params.set("limit", String(options.limit));

    const response = await fetch(`${API_BASE}/scanner/items?${params}`);
    if (!response.ok) throw new Error("Failed to fetch items");
    return response.json();
  },

  async getItem(id: string): Promise<FashionItem> {
    const response = await fetch(`${API_BASE}/scanner/items/${id}`);
    if (!response.ok) throw new Error("Item not found");
    return response.json();
  },

  async getAnalysis(): Promise<{ data: TrendAnalysis }> {
    const response = await fetch(`${API_BASE}/scanner/analysis`);
    if (!response.ok) throw new Error("No analysis available");
    return response.json();
  },

  async getCategories(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/scanner/categories`);
    if (!response.ok) throw new Error("Failed to fetch categories");
    return response.json();
  },
};

/**
 * Generator API
 */
export const generator = {
  async generate(
    sourceImageId: string,
    options?: {
      style?: string;
      variationStrength?: number;
      numVariations?: number;
      colorPalette?: { primary: string; secondary?: string; accent?: string };
      promptAdditions?: string;
    }
  ): Promise<GenerationResult> {
    const response = await fetch(`${API_BASE}/generator/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_image_id: sourceImageId,
        style: options?.style || "minimalist",
        variation_strength: options?.variationStrength || 0.5,
        num_variations: options?.numVariations || 4,
        color_palette: options?.colorPalette,
        prompt_additions: options?.promptAdditions,
      }),
    });
    if (!response.ok) throw new Error("Generation failed");
    return response.json();
  },

  async quickGenerate(
    itemId: string,
    style = "minimalist",
    count = 4
  ): Promise<GenerationResult> {
    const params = new URLSearchParams({
      item_id: itemId,
      style,
      count: String(count),
    });
    const response = await fetch(`${API_BASE}/generator/generate/quick?${params}`, {
      method: "POST",
    });
    if (!response.ok) throw new Error("Generation failed");
    return response.json();
  },

  async getDesigns(options?: {
    sourceItemId?: string;
    style?: string;
    limit?: number;
  }): Promise<GeneratedDesign[]> {
    const params = new URLSearchParams();
    if (options?.sourceItemId) params.set("source_item_id", options.sourceItemId);
    if (options?.style) params.set("style", options.style);
    if (options?.limit) params.set("limit", String(options.limit));

    const response = await fetch(`${API_BASE}/generator/designs?${params}`);
    if (!response.ok) throw new Error("Failed to fetch designs");
    return response.json();
  },

  async getStyles(): Promise<Array<{ id: string; name: string; description: string }>> {
    const response = await fetch(`${API_BASE}/generator/styles`);
    if (!response.ok) throw new Error("Failed to fetch styles");
    return response.json();
  },
};

/**
 * Converter API
 */
export const converter = {
  async convert(
    sourceImageId: string,
    options?: {
      style?: string;
      detailLevel?: number;
      lineThickness?: number;
      includeMeasurements?: boolean;
    }
  ): Promise<ConversionResult> {
    const response = await fetch(`${API_BASE}/converter/convert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_image_id: sourceImageId,
        style: options?.style || "technical",
        detail_level: options?.detailLevel || 0.5,
        line_thickness: options?.lineThickness || 1.0,
        include_measurements: options?.includeMeasurements || false,
      }),
    });
    if (!response.ok) throw new Error("Conversion failed");
    return response.json();
  },

  async quickConvert(itemId: string, style = "technical"): Promise<ConversionResult> {
    const params = new URLSearchParams({ item_id: itemId, style });
    const response = await fetch(`${API_BASE}/converter/convert/quick?${params}`, {
      method: "POST",
    });
    if (!response.ok) throw new Error("Conversion failed");
    return response.json();
  },

  async getSketches(options?: {
    sourceItemId?: string;
    style?: string;
    limit?: number;
  }): Promise<ConvertedSketch[]> {
    const params = new URLSearchParams();
    if (options?.sourceItemId) params.set("source_item_id", options.sourceItemId);
    if (options?.style) params.set("style", options.style);
    if (options?.limit) params.set("limit", String(options.limit));

    const response = await fetch(`${API_BASE}/converter/sketches?${params}`);
    if (!response.ok) throw new Error("Failed to fetch sketches");
    return response.json();
  },

  async getStyles(): Promise<Array<{ id: string; name: string; description: string }>> {
    const response = await fetch(`${API_BASE}/converter/styles`);
    if (!response.ok) throw new Error("Failed to fetch styles");
    return response.json();
  },
};

/**
 * Health check
 */
export async function checkHealth(): Promise<{
  status: string;
  version: string;
  demo_mode: boolean;
}> {
  const response = await fetch("/health");
  if (!response.ok) throw new Error("API not available");
  return response.json();
}
