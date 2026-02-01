"""
Pydantic models for TrendMuse API
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FashionCategory(str, Enum):
    """Fashion item categories"""
    DRESS = "dress"
    TOP = "top"
    PANTS = "pants"
    SKIRT = "skirt"
    JACKET = "jacket"
    COAT = "coat"
    SHOES = "shoes"
    ACCESSORIES = "accessories"
    SWIMWEAR = "swimwear"
    ACTIVEWEAR = "activewear"


class TrendLevel(str, Enum):
    """Trend popularity levels"""
    HOT = "hot"
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"


# ============ Scanner Models ============

class ScanRequest(BaseModel):
    """Request to scan a website for fashion items"""
    url: str = Field(..., description="Website URL to scan")
    max_items: int = Field(default=20, ge=1, le=100, description="Maximum items to fetch")
    category_filter: Optional[FashionCategory] = Field(default=None, description="Filter by category")


class FashionItem(BaseModel):
    """A scraped fashion item"""
    id: str
    name: str
    price: float
    currency: str = "USD"
    original_price: Optional[float] = None
    image_url: str
    local_image_path: Optional[str] = None
    product_url: str
    category: FashionCategory
    brand: str
    reviews_count: int = 0
    rating: float = 0.0
    sales_count: int = 0
    trend_score: float = Field(default=0.0, ge=0, le=100)
    trend_level: TrendLevel = TrendLevel.STABLE
    colors: List[str] = []
    tags: List[str] = []
    scraped_at: datetime = Field(default_factory=datetime.now)


class ScanResult(BaseModel):
    """Result of a website scan"""
    source_url: str
    items: List[FashionItem]
    total_found: int
    scan_duration_ms: int
    timestamp: datetime = Field(default_factory=datetime.now)


# ============ Generator Models ============

class GenerationStyle(str, Enum):
    """Design generation styles"""
    MINIMALIST = "minimalist"
    AVANT_GARDE = "avant-garde"
    BOHEMIAN = "bohemian"
    STREETWEAR = "streetwear"
    VINTAGE = "vintage"
    FUTURISTIC = "futuristic"


class ColorPalette(BaseModel):
    """Color palette for generation"""
    primary: str = Field(..., description="Primary color hex code")
    secondary: Optional[str] = Field(default=None, description="Secondary color hex code")
    accent: Optional[str] = Field(default=None, description="Accent color hex code")


class GenerateRequest(BaseModel):
    """Request to generate design variations"""
    source_image_id: str = Field(..., description="ID of the source fashion item")
    style: GenerationStyle = Field(default=GenerationStyle.MINIMALIST)
    variation_strength: float = Field(default=0.5, ge=0.1, le=1.0, description="How different from original (0.1=subtle, 1.0=dramatic)")
    color_palette: Optional[ColorPalette] = None
    num_variations: int = Field(default=4, ge=1, le=8)
    prompt_additions: Optional[str] = Field(default=None, description="Additional prompt text")


class GeneratedDesign(BaseModel):
    """A generated design variation"""
    id: str
    source_item_id: str
    image_url: str
    local_image_path: Optional[str] = None
    style: GenerationStyle
    variation_strength: float
    generation_prompt: str
    created_at: datetime = Field(default_factory=datetime.now)


class GenerationResult(BaseModel):
    """Result of design generation"""
    source_item: FashionItem
    variations: List[GeneratedDesign]
    generation_time_ms: int


# ============ Converter Models ============

class SketchStyle(str, Enum):
    """Sketch conversion styles"""
    TECHNICAL = "technical"
    FASHION_ILLUSTRATION = "fashion_illustration"
    PENCIL = "pencil"
    INK = "ink"
    WATERCOLOR = "watercolor"


class ConvertRequest(BaseModel):
    """Request to convert image to sketch"""
    source_image_id: str = Field(..., description="ID of the source fashion item")
    style: SketchStyle = Field(default=SketchStyle.TECHNICAL)
    detail_level: float = Field(default=0.5, ge=0.1, le=1.0, description="Amount of detail (0.1=minimal, 1.0=detailed)")
    line_thickness: float = Field(default=1.0, ge=0.5, le=3.0)
    include_measurements: bool = Field(default=False, description="Add measurement annotations")


class ConvertedSketch(BaseModel):
    """A converted sketch"""
    id: str
    source_item_id: str
    image_url: str
    local_image_path: Optional[str] = None
    style: SketchStyle
    detail_level: float
    created_at: datetime = Field(default_factory=datetime.now)


class ConversionResult(BaseModel):
    """Result of sketch conversion"""
    source_item: FashionItem
    sketch: ConvertedSketch
    conversion_time_ms: int


# ============ API Response Models ============

class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    demo_mode: bool
