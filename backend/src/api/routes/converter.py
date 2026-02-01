"""
Converter API Routes

Endpoints for converting fashion photos to sketches.
"""
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path

from src.models.schemas import (
    ConvertRequest,
    ConversionResult,
    ConvertedSketch,
    SketchStyle,
    FashionItem
)
from src.services.sketch_converter import SketchConverterService
from src.core.config import get_settings

router = APIRouter(prefix="/converter", tags=["Converter"])

# In-memory storage for demo
_converted_sketches: List[ConvertedSketch] = []

# Import scanned items from scanner module
from .scanner import _scanned_items


def _get_item_by_id(item_id: str) -> Optional[FashionItem]:
    """Get fashion item by ID from scanned items"""
    for item in _scanned_items:
        if item.id == item_id:
            return item
    return None


@router.post("/convert", response_model=ConversionResult)
async def convert_to_sketch(request: ConvertRequest):
    """
    Convert a fashion item image to sketch style
    
    In demo mode, uses edge detection filters.
    Can be upgraded to ControlNet for production quality.
    """
    global _converted_sketches
    
    start_time = time.time()
    
    # Get source item
    source_item = _get_item_by_id(request.source_image_id)
    if not source_item:
        raise HTTPException(
            status_code=404,
            detail=f"Source item not found: {request.source_image_id}"
        )
    
    try:
        # Convert to sketch
        service = SketchConverterService()
        sketch = await service.convert_to_sketch(
            source_item=source_item,
            style=request.style,
            detail_level=request.detail_level,
            line_thickness=request.line_thickness,
            include_measurements=request.include_measurements
        )
        
        # Store for later retrieval
        _converted_sketches.append(sketch)
        
        # Calculate conversion time
        conversion_time_ms = int((time.time() - start_time) * 1000)
        
        return ConversionResult(
            source_item=source_item,
            sketch=sketch,
            conversion_time_ms=conversion_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/sketches", response_model=List[ConvertedSketch])
async def get_converted_sketches(
    source_item_id: Optional[str] = Query(None, description="Filter by source item"),
    style: Optional[SketchStyle] = Query(None, description="Filter by style"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    Get previously converted sketches
    """
    sketches = _converted_sketches.copy()
    
    # Filter by source item
    if source_item_id:
        sketches = [s for s in sketches if s.source_item_id == source_item_id]
    
    # Filter by style
    if style:
        sketches = [s for s in sketches if s.style == style]
    
    # Sort by creation time (newest first)
    sketches.sort(key=lambda x: x.created_at, reverse=True)
    
    return sketches[:limit]


@router.get("/sketches/{sketch_id}", response_model=ConvertedSketch)
async def get_sketch_by_id(sketch_id: str):
    """
    Get a specific sketch by ID
    """
    for sketch in _converted_sketches:
        if sketch.id == sketch_id:
            return sketch
    
    raise HTTPException(status_code=404, detail="Sketch not found")


@router.get("/styles", response_model=List[dict])
async def get_available_sketch_styles():
    """
    Get list of available sketch styles with descriptions
    """
    styles = [
        {
            "id": SketchStyle.TECHNICAL.value,
            "name": "Technical Drawing",
            "description": "Clean lines, blueprint style, ideal for production"
        },
        {
            "id": SketchStyle.FASHION_ILLUSTRATION.value,
            "name": "Fashion Illustration",
            "description": "Elegant, artistic style like magazine sketches"
        },
        {
            "id": SketchStyle.PENCIL.value,
            "name": "Pencil Sketch",
            "description": "Classic hand-drawn pencil look"
        },
        {
            "id": SketchStyle.INK.value,
            "name": "Ink Drawing",
            "description": "Bold lines, high contrast ink style"
        },
        {
            "id": SketchStyle.WATERCOLOR.value,
            "name": "Watercolor",
            "description": "Soft, artistic watercolor illustration"
        },
    ]
    return styles


@router.post("/convert/quick")
async def quick_convert(
    item_id: str = Query(..., description="Source item ID"),
    style: SketchStyle = Query(SketchStyle.TECHNICAL, description="Sketch style")
):
    """
    Quick conversion endpoint with minimal parameters
    """
    request = ConvertRequest(
        source_image_id=item_id,
        style=style
    )
    return await convert_to_sketch(request)


@router.delete("/sketches/{sketch_id}")
async def delete_sketch(sketch_id: str):
    """
    Delete a converted sketch
    """
    global _converted_sketches
    
    for i, sketch in enumerate(_converted_sketches):
        if sketch.id == sketch_id:
            # Also delete local file if exists
            if sketch.local_image_path:
                try:
                    Path(sketch.local_image_path).unlink(missing_ok=True)
                except:
                    pass
            
            _converted_sketches.pop(i)
            return {"success": True, "message": "Sketch deleted"}
    
    raise HTTPException(status_code=404, detail="Sketch not found")


# Serve sketch images
@router.get("/image/{sketch_id}")
async def get_sketch_image(sketch_id: str):
    """
    Get the sketch image file
    """
    settings = get_settings()
    
    # Try to find the sketch
    for sketch in _converted_sketches:
        if sketch.id == sketch_id:
            if sketch.local_image_path and Path(sketch.local_image_path).exists():
                return FileResponse(sketch.local_image_path, media_type="image/png")
    
    # Also check by direct file path
    file_path = settings.sketches_dir / f"{sketch_id}.png"
    if file_path.exists():
        return FileResponse(str(file_path), media_type="image/png")
    
    raise HTTPException(status_code=404, detail="Sketch image not found")
