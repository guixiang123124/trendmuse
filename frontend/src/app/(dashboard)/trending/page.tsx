"use client";

import { useState, useEffect, useRef } from "react";

interface Product {
  id: string;
  name: string;
  price: number;
  source: string;
  image_url: string;
  product_url: string;
  category?: string;
  brand?: string;
}

interface BrandGroup {
  brand_name: string;
  total_count: number;
  products: Product[];
}

export default function TrendingPage() {
  const [brandData, setBrandData] = useState<Record<string, BrandGroup>>({});
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [generatedFrom, setGeneratedFrom] = useState<string | null>(null);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [customUrl, setCustomUrl] = useState("");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadTrendingProducts();
  }, []);

  const loadTrendingProducts = async () => {
    try {
      // 从后端获取按品牌分组的产品
      const res = await fetch("/api/trends/products-by-brand?items_per_brand=10");
      if (res.ok) {
        const data = await res.json();
        setBrandData(data.brands || {});
      } else {
        throw new Error("API error");
      }
    } catch (error) {
      console.error("Error loading products:", error);
      // Fallback to old API
      try {
        const res = await fetch("/api/trends/products?limit=100");
        if (res.ok) {
          const data = await res.json();
          // Group by source manually
          const grouped: Record<string, BrandGroup> = {};
          for (const p of data.products || []) {
            const source = p.source || 'unknown';
            if (!grouped[source]) {
              grouped[source] = {
                brand_name: source.replace('.com', '').replace('www.', ''),
                total_count: 0,
                products: []
              };
            }
            if (grouped[source].products.length < 10) {
              grouped[source].products.push(p);
            }
            grouped[source].total_count++;
          }
          setBrandData(grouped);
        }
      } catch (e) {
        console.error("Fallback also failed:", e);
      }
    }
    setLoading(false);
  };

  const handleRedesign = async (product: Product) => {
    setGenerating(product.id);
    setGeneratedImage(null);
    setGeneratedFrom(product.name);
    
    try {
      const params = new URLSearchParams({
        product_name: product.name,
        style_variation: "similar",
        ...(product.image_url && { reference_url: product.image_url })
      });
      
      const res = await fetch(`/api/generator/redesign?${params}`, {
        method: "POST"
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.image_url) {
          setGeneratedImage(data.image_url);
        } else {
          throw new Error("No image returned");
        }
      } else {
        const error = await res.json();
        console.error("API error:", error);
        alert(`Generation failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Generation error:", error);
      alert("Generation failed. Please try again.");
    }
    
    setGenerating(null);
  };

  const handleGenerateFromUrl = async () => {
    if (!customUrl && !uploadedImage) {
      alert("Please provide an image URL or upload an image");
      return;
    }
    
    const imageUrl = uploadedImage || customUrl;
    setGenerating("custom");
    setGeneratedImage(null);
    setGeneratedFrom("Custom Image");
    setShowUploadModal(false);
    
    try {
      const params = new URLSearchParams({
        reference_url: imageUrl,
        style_variation: "similar"
      });
      
      const res = await fetch(`/api/generator/redesign?${params}`, {
        method: "POST"
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.image_url) {
          setGeneratedImage(data.image_url);
        } else {
          throw new Error("No image returned");
        }
      } else {
        const error = await res.json();
        alert(`Generation failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Generation error:", error);
      alert("Generation failed. Please try again.");
    }
    
    setGenerating(null);
    setUploadedImage(null);
    setCustomUrl("");
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setUploadedImage(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const brandEntries = Object.entries(brandData);

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%)",
      padding: "2rem"
    }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ 
              fontSize: "2rem", 
              fontWeight: "bold", 
              color: "white",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem"
            }}>
              🔥 Trending Products
            </h1>
            <p style={{ color: "#94a3b8", marginTop: "0.5rem" }}>
              {brandEntries.length} 个品牌的热销款 - 点击 Redesign 生成类似风格设计
            </p>
          </div>
          
          {/* Upload Button */}
          <button
            onClick={() => setShowUploadModal(true)}
            style={{
              padding: "12px 24px",
              background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "1rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            📤 上传图片生成
          </button>
        </div>

        {loading ? (
          <p style={{ color: "white", textAlign: "center", padding: "4rem" }}>Loading...</p>
        ) : brandEntries.length === 0 ? (
          <p style={{ color: "#94a3b8", textAlign: "center", padding: "4rem" }}>
            No products found. Run a scrape first.
          </p>
        ) : (
          /* Products by Brand */
          brandEntries.map(([source, group]) => (
            <div key={source} style={{ marginBottom: "3rem" }}>
              {/* Brand Header */}
              <div style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: "1rem", 
                marginBottom: "1rem",
                borderBottom: "1px solid #334155",
                paddingBottom: "0.75rem"
              }}>
                <h2 style={{ 
                  color: "white", 
                  fontSize: "1.5rem",
                  margin: 0
                }}>
                  {group.brand_name}
                </h2>
                <span style={{ 
                  color: "#64748b", 
                  fontSize: "0.9rem",
                  background: "rgba(51, 65, 85, 0.5)",
                  padding: "4px 12px",
                  borderRadius: "12px"
                }}>
                  {group.total_count} products
                </span>
                <a 
                  href={`https://${source}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#8b5cf6", fontSize: "0.85rem", marginLeft: "auto" }}
                >
                  Visit Store →
                </a>
              </div>

              {/* Products Grid */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                gap: "1rem"
              }}>
                {group.products.map((product, idx) => (
                  <div key={product.id || idx} style={{
                    background: "rgba(30, 41, 59, 0.8)",
                    borderRadius: "12px",
                    overflow: "hidden",
                    border: "1px solid #334155",
                    transition: "transform 0.2s",
                  }}>
                    {/* Product Image */}
                    <div style={{ 
                      aspectRatio: "1", 
                      position: "relative",
                      background: "#1e293b"
                    }}>
                      {product.image_url ? (
                        <img 
                          src={product.image_url} 
                          alt={product.name}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover"
                          }}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <div style={{
                          width: "100%",
                          height: "100%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#64748b"
                        }}>
                          No Image
                        </div>
                      )}
                      
                      {/* Category Badge */}
                      {product.category && (
                        <span style={{
                          position: "absolute",
                          top: "8px",
                          left: "8px",
                          background: "rgba(139, 92, 246, 0.8)",
                          color: "white",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "11px"
                        }}>
                          {product.category}
                        </span>
                      )}
                    </div>

                    {/* Product Info */}
                    <div style={{ padding: "0.75rem" }}>
                      <h3 style={{ 
                        color: "white", 
                        fontSize: "0.85rem",
                        marginBottom: "0.5rem",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        lineHeight: "1.3"
                      }}>
                        {product.name}
                      </h3>
                      
                      <div style={{ 
                        display: "flex", 
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "0.5rem"
                      }}>
                        <span style={{ color: "#a78bfa", fontWeight: "bold", fontSize: "0.9rem" }}>
                          ${product.price?.toFixed(2) || '0.00'}
                        </span>
                      </div>

                      {/* Action Buttons */}
                      <div style={{ display: "flex", gap: "0.4rem" }}>
                        <a 
                          href={product.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            flex: 1,
                            padding: "6px 8px",
                            background: "#334155",
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            textAlign: "center",
                            textDecoration: "none",
                            fontSize: "0.75rem",
                            cursor: "pointer"
                          }}
                        >
                          View
                        </a>
                        <button
                          onClick={() => handleRedesign(product)}
                          disabled={generating === product.id}
                          style={{
                            flex: 1,
                            padding: "6px 8px",
                            background: generating === product.id 
                              ? "#64748b" 
                              : "linear-gradient(135deg, #8b5cf6, #ec4899)",
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            fontSize: "0.75rem",
                            cursor: generating === product.id ? "wait" : "pointer"
                          }}
                        >
                          {generating === product.id ? "⏳..." : "🎨 Redesign"}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}

        {/* Upload Modal */}
        {showUploadModal && (
          <div style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }} onClick={() => setShowUploadModal(false)}>
            <div style={{
              background: "#1e293b",
              borderRadius: "12px",
              padding: "2rem",
              maxWidth: "500px",
              width: "90%"
            }} onClick={e => e.stopPropagation()}>
              <h3 style={{ color: "white", marginBottom: "1.5rem", fontSize: "1.25rem" }}>
                📤 上传图片或输入 URL
              </h3>
              
              {/* File Upload */}
              <div style={{ marginBottom: "1.5rem" }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  style={{ display: "none" }}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    width: "100%",
                    padding: "1.5rem",
                    background: uploadedImage ? "#22c55e" : "#334155",
                    color: "white",
                    border: "2px dashed #64748b",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "1rem"
                  }}
                >
                  {uploadedImage ? "✅ 图片已上传" : "📁 点击选择本地图片"}
                </button>
                {uploadedImage && (
                  <img 
                    src={uploadedImage} 
                    alt="Preview"
                    style={{ 
                      width: "100%", 
                      maxHeight: "200px", 
                      objectFit: "contain",
                      marginTop: "1rem",
                      borderRadius: "8px"
                    }}
                  />
                )}
              </div>
              
              <div style={{ 
                color: "#64748b", 
                textAlign: "center", 
                margin: "1rem 0",
                position: "relative"
              }}>
                <span style={{ background: "#1e293b", padding: "0 1rem" }}>或</span>
                <div style={{ 
                  position: "absolute", 
                  top: "50%", 
                  left: 0, 
                  right: 0, 
                  height: "1px", 
                  background: "#334155",
                  zIndex: -1
                }} />
              </div>
              
              {/* URL Input */}
              <div style={{ marginBottom: "1.5rem" }}>
                <input
                  type="text"
                  placeholder="输入图片 URL..."
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    background: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    color: "white",
                    fontSize: "1rem"
                  }}
                />
              </div>
              
              {/* Actions */}
              <div style={{ display: "flex", gap: "1rem" }}>
                <button
                  onClick={() => setShowUploadModal(false)}
                  style={{
                    flex: 1,
                    padding: "12px",
                    background: "#334155",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer"
                  }}
                >
                  取消
                </button>
                <button
                  onClick={handleGenerateFromUrl}
                  disabled={!uploadedImage && !customUrl}
                  style={{
                    flex: 1,
                    padding: "12px",
                    background: (!uploadedImage && !customUrl) 
                      ? "#64748b" 
                      : "linear-gradient(135deg, #8b5cf6, #ec4899)",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: (!uploadedImage && !customUrl) ? "not-allowed" : "pointer"
                  }}
                >
                  🎨 生成设计
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Generated Image Modal */}
        {generatedImage && (
          <div style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }} onClick={() => setGeneratedImage(null)}>
            <div style={{
              background: "#1e293b",
              borderRadius: "12px",
              padding: "1.5rem",
              maxWidth: "600px",
              width: "90%"
            }} onClick={e => e.stopPropagation()}>
              <h3 style={{ color: "white", marginBottom: "0.5rem" }}>
                🎨 AI Generated Design
              </h3>
              {generatedFrom && (
                <p style={{ color: "#94a3b8", fontSize: "0.85rem", marginBottom: "1rem" }}>
                  Based on: {generatedFrom}
                </p>
              )}
              <img 
                src={generatedImage} 
                alt="Generated Design"
                style={{
                  width: "100%",
                  borderRadius: "8px",
                  marginBottom: "1rem"
                }}
              />
              <div style={{ display: "flex", gap: "0.75rem" }}>
                <a
                  href={generatedImage}
                  download="trendmuse-design.png"
                  target="_blank"
                  style={{
                    flex: 1,
                    padding: "10px",
                    background: "#8b5cf6",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    textAlign: "center",
                    textDecoration: "none"
                  }}
                >
                  📥 Download
                </a>
                <button
                  onClick={() => setGeneratedImage(null)}
                  style={{
                    flex: 1,
                    padding: "10px",
                    background: "#334155",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer"
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Generating Overlay */}
        {generating && (
          <div style={{
            position: "fixed",
            bottom: "2rem",
            right: "2rem",
            background: "#1e293b",
            padding: "1rem 1.5rem",
            borderRadius: "12px",
            border: "1px solid #334155",
            boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            zIndex: 999
          }}>
            <div style={{
              width: "20px",
              height: "20px",
              border: "2px solid #8b5cf6",
              borderTopColor: "transparent",
              borderRadius: "50%",
              animation: "spin 1s linear infinite"
            }} />
            <span style={{ color: "white" }}>Generating design...</span>
            <style>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}
      </div>
    </div>
  );
}
