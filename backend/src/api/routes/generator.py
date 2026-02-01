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
    ColorPalette
)
from src.services.image_gen import ImageGenerationService
from src.core.config import get_settings

router = APIRouter(prefix="/generator", tags=["Generator"])

# In-memory storage for demo
_generated_designs: List[GeneratedDesign] = []

# Import scanned items from scanner module
from .scanner import _scanned_items


def _get_item_by_id(item_id: str) -> Optional[FashionItem]:
    """Get fashion item by ID from scanned items"""
    for item in _scanned_items:
        if item.id == item_id:
            return item
    return None


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
