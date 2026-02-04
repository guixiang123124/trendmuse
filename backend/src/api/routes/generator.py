"""
Generator API Routes

Endpoints for generating design variations using AI.
"""
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from src.models.schemas import (
    GenerateRequest,
    GenerationResult,
    GeneratedDesign,
    GenerationStyle,
    FashionItem,
    FashionCategory,
    ColorPalette
)
from src.services.image_gen import ImageGenerationService
from src.services.database import get_database
from src.core.config import get_settings

router = APIRouter(prefix="/generator", tags=["Generator"])

# In-memory storage for demo
_generated_designs: List[GeneratedDesign] = []

# Import scanned items from scanner module (fallback)
from .scanner import _scanned_items


def _get_item_by_id(item_id: str) -> Optional[FashionItem]:
    """Get fashion item by ID from scanned items or database"""
    # First check in-memory items
    for item in _scanned_items:
        if item.id == item_id:
            return item
    
    # Then check database
    db = get_database()
    # Try to find by ID in database
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            product = db._row_to_dict(row)
            # Convert to FashionItem
            return FashionItem(
                id=product['id'],
                name=product['name'],
                price=product['price'] or 0,
                currency=product.get('currency', 'USD'),
                original_price=product.get('original_price'),
                image_url=product.get('image_url', ''),
                product_url=product.get('product_url', ''),
                category=FashionCategory(product.get('category', 'other')),
                brand=product.get('brand', ''),
                reviews_count=product.get('reviews_count', 0),
                rating=product.get('rating', 0),
                sales_count=0,
                trend_score=50,
                trend_level="stable",
                colors=product.get('colors', []),
                tags=product.get('tags', [])
            )
    
    return None


@router.get("/items-from-db")
async def get_items_from_database(
    limit: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Get fashion items from database for the generator.
    Returns items with images that can be used for AI generation.
    """
    db = get_database()
    products = db.get_products(source=source, category=category, limit=limit)
    
    # Convert to format expected by frontend
    items = []
    for p in products:
        if p.get('image_url'):  # Only include items with images
            items.append({
                "id": p['id'],
                "name": p['name'],
                "price": p.get('price', 0),
                "image_url": p['image_url'],
                "category": p.get('category', 'other'),
                "brand": p.get('brand', ''),
                "source": p.get('source', '')
            })
    
    return items


@router.post("/generate", response_model=GenerationResult)
async def generate_design_variations(request: GenerateRequest):
    """
    Generate design variations for a fashion item
    
    In demo mode, returns placeholder variations.
    With Replicate API configured, generates actual AI variations.
    """
    global _generated_designs
    
    start_time = time.time()
    
    # Get source item
    source_item = _get_item_by_id(request.source_image_id)
    if not source_item:
        raise HTTPException(
            status_code=404, 
            detail=f"Source item not found: {request.source_image_id}"
        )
    
    try:
        # Generate variations
        service = ImageGenerationService()
        variations = await service.generate_variations(
            source_item=source_item,
            style=request.style,
            variation_strength=request.variation_strength,
            color_palette=request.color_palette,
            num_variations=request.num_variations,
            prompt_additions=request.prompt_additions
        )
        
        # Store for later retrieval
        _generated_designs.extend(variations)
        
        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        return GenerationResult(
            source_item=source_item,
            variations=variations,
            generation_time_ms=generation_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/designs", response_model=List[GeneratedDesign])
async def get_generated_designs(
    source_item_id: Optional[str] = Query(None, description="Filter by source item"),
    style: Optional[GenerationStyle] = Query(None, description="Filter by style"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    Get previously generated designs
    """
    designs = _generated_designs.copy()
    
    # Filter by source item
    if source_item_id:
        designs = [d for d in designs if d.source_item_id == source_item_id]
    
    # Filter by style
    if style:
        designs = [d for d in designs if d.style == style]
    
    # Sort by creation time (newest first)
    designs.sort(key=lambda x: x.created_at, reverse=True)
    
    return designs[:limit]


@router.get("/designs/{design_id}", response_model=GeneratedDesign)
async def get_design_by_id(design_id: str):
    """
    Get a specific generated design by ID
    """
    for design in _generated_designs:
        if design.id == design_id:
            return design
    
    raise HTTPException(status_code=404, detail="Design not found")


@router.get("/styles", response_model=List[dict])
async def get_available_styles():
    """
    Get list of available generation styles with descriptions
    """
    styles = [
        {
            "id": GenerationStyle.MINIMALIST.value,
            "name": "Minimalist",
            "description": "Clean lines, simple design, modern aesthetic"
        },
        {
            "id": GenerationStyle.AVANT_GARDE.value,
            "name": "Avant-Garde",
            "description": "Experimental, high fashion, artistic approach"
        },
        {
            "id": GenerationStyle.BOHEMIAN.value,
            "name": "Bohemian",
            "description": "Flowy, natural, earthy and relaxed vibes"
        },
        {
            "id": GenerationStyle.STREETWEAR.value,
            "name": "Streetwear",
            "description": "Urban, edgy, contemporary casual cool"
        },
        {
            "id": GenerationStyle.VINTAGE.value,
            "name": "Vintage",
            "description": "Retro, classic, timeless and nostalgic"
        },
        {
            "id": GenerationStyle.FUTURISTIC.value,
            "name": "Futuristic",
            "description": "Metallic, innovative, tech-inspired designs"
        },
    ]
    return styles


@router.post("/generate/quick")
async def quick_generate(
    item_id: str = Query(..., description="Source item ID"),
    style: GenerationStyle = Query(GenerationStyle.MINIMALIST, description="Generation style"),
    count: int = Query(4, ge=1, le=8, description="Number of variations")
):
    """
    Quick generation endpoint with minimal parameters
    """
    request = GenerateRequest(
        source_image_id=item_id,
        style=style,
        num_variations=count
    )
    return await generate_design_variations(request)


@router.delete("/designs/{design_id}")
async def delete_design(design_id: str):
    """
    Delete a generated design
    """
    global _generated_designs
    
    for i, design in enumerate(_generated_designs):
        if design.id == design_id:
            _generated_designs.pop(i)
            return {"success": True, "message": "Design deleted"}
    
    raise HTTPException(status_code=404, detail="Design not found")


@router.post("/redesign")
async def redesign_product(
    prompt: Optional[str] = Query(None, description="Custom design prompt (optional)"),
    reference_url: Optional[str] = Query(None, description="Reference image URL"),
    product_name: Optional[str] = Query(None, description="Product name for smart prompt"),
    style_variation: str = Query("similar", description="Variation style: similar, bold, minimal, colorful")
):
    """
    Generate a new design based on reference image using GrsAI API.
    
    Nano Banana is a world-understanding model that can intelligently 
    create variations based on the original garment's theme, pattern, and style.
    
    If no custom prompt is provided, uses smart prompt generation based on product name.
    """
    import httpx
    import json
    
    settings = get_settings()
    api_key = settings.grsai_api_key
    api_base = settings.grsai_api_base
    model = settings.grsai_model
    
    if not api_key:
        raise HTTPException(status_code=500, detail="GrsAI API key not configured")
    
    # Smart prompt generation if no custom prompt
    if not prompt:
        if product_name:
            # Style-specific variations
            style_hints = {
                "similar": "保持相似的整体风格，微调细节",
                "bold": "更大胆的配色和图案",
                "minimal": "更简约的设计风格",
                "colorful": "更丰富的色彩搭配"
            }
            style_hint = style_hints.get(style_variation, "")
            
            prompt = f"""根据这件 {product_name} 的主题、印花和风格 pattern，
生成一个同样版型但不同变体风格的童装设计。
{style_hint}
保持专业的产品图风格，白色背景，适合电商展示。"""
        else:
            prompt = """根据这件衣服的主题、印花和风格 pattern，
生成一个同样版型但不同变体风格的设计。
保持专业的产品图风格，白色背景，适合电商展示。"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "aspectRatio": "1:1"
    }
    
    if reference_url:
        payload["urls"] = [reference_url]
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{api_base}/v1/draw/nano-banana",
                headers=headers,
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(status_code=response.status_code, detail=f"GrsAI API error: {error_text}")
                
                async for line in response.aiter_lines():
                    if line and line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            status = data.get("status", "").lower()
                            
                            if status == "succeeded":
                                results = data.get("results", [])
                                if results and results[0].get("url"):
                                    return {
                                        "success": True,
                                        "image_url": results[0]["url"],
                                        "prompt": prompt,
                                        "style_variation": style_variation
                                    }
                            elif status == "failed":
                                raise HTTPException(
                                    status_code=500,
                                    detail=f"Generation failed: {data.get('failure_reason', 'Unknown')}"
                                )
                        except json.JSONDecodeError:
                            continue
                
                raise HTTPException(status_code=500, detail="No result received from GrsAI")
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-url")
async def generate_from_url(
    image_url: str = Query(..., description="Image URL to use as reference"),
    prompt: Optional[str] = Query(None, description="Custom prompt"),
    style: str = Query("similar", description="Style variation: similar, bold, minimal, colorful"),
    count: int = Query(1, ge=1, le=4, description="Number of variations")
):
    """
    Generate design variations directly from an image URL.
    No need to have the product in our database.
    """
    results = []
    
    for i in range(count):
        result = await redesign_product(
            prompt=prompt,
            reference_url=image_url,
            style_variation=style
        )
        if result.get("success"):
            results.append(result["image_url"])
    
    return {
        "success": True,
        "source_url": image_url,
        "generated_images": results,
        "count": len(results)
    }
