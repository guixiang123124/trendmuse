"""
Scanner API Routes

Endpoints for scanning fashion e-commerce websites and analyzing trends.
"""
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from src.models.schemas import (
    ScanRequest, 
    ScanResult, 
    FashionItem,
    FashionCategory,
    APIResponse
)
from src.services.scraper import MockScraper, GenericScraper
from src.services.analyzer import TrendAnalyzer
from src.core.config import get_settings

router = APIRouter(prefix="/scanner", tags=["Scanner"])

# In-memory storage for demo (use database in production)
_scanned_items: List[FashionItem] = []
_last_scan_result: Optional[ScanResult] = None


@router.post("/scan", response_model=ScanResult)
async def scan_website(request: ScanRequest):
    """
    Scan a fashion e-commerce website for trending items
    
    In demo mode, returns mock fashion data.
    With Playwright configured, will scrape actual websites.
    """
    global _scanned_items, _last_scan_result
    
    settings = get_settings()
    start_time = time.time()
    
    try:
        # Choose scraper based on mode
        if settings.demo_mode:
            scraper = MockScraper(timeout=settings.scrape_timeout)
        else:
            scraper = GenericScraper(timeout=settings.scrape_timeout)
        
        # Perform scan
        items = await scraper.scrape(
            url=request.url,
            max_items=min(request.max_items, settings.max_items_per_scan),
            category_filter=request.category_filter
        )
        
        # Store items for later use
        _scanned_items = items
        
        # Calculate scan duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        result = ScanResult(
            source_url=request.url,
            items=items,
            total_found=len(items),
            scan_duration_ms=duration_ms,
            timestamp=datetime.now()
        )
        
        _last_scan_result = result
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/items", response_model=List[FashionItem])
async def get_scanned_items(
    category: Optional[FashionCategory] = Query(None, description="Filter by category"),
    min_trend_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum trend score"),
    sort_by: str = Query("trend_score", description="Sort field: trend_score, price, reviews_count"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return")
):
    """
    Get previously scanned items with optional filtering and sorting
    """
    items = _scanned_items.copy()
    
    # Filter by category
    if category:
        items = [item for item in items if item.category == category]
    
    # Filter by trend score
    if min_trend_score is not None:
        items = [item for item in items if item.trend_score >= min_trend_score]
    
    # Sort
    sort_reverse = True
    if sort_by == "price":
        items.sort(key=lambda x: x.price, reverse=sort_reverse)
    elif sort_by == "reviews_count":
        items.sort(key=lambda x: x.reviews_count, reverse=sort_reverse)
    else:
        items.sort(key=lambda x: x.trend_score, reverse=sort_reverse)
    
    return items[:limit]


@router.get("/items/{item_id}", response_model=FashionItem)
async def get_item_by_id(item_id: str):
    """
    Get a specific fashion item by ID
    """
    for item in _scanned_items:
        if item.id == item_id:
            return item
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.get("/analysis")
async def get_trend_analysis():
    """
    Get comprehensive trend analysis of scanned items
    """
    if not _scanned_items:
        raise HTTPException(
            status_code=400, 
            detail="No items scanned yet. Run a scan first."
        )
    
    analyzer = TrendAnalyzer()
    analysis = analyzer.analyze_items(_scanned_items)
    
    return {
        "success": True,
        "data": analysis,
        "items_analyzed": len(_scanned_items),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/categories", response_model=List[str])
async def get_available_categories():
    """
    Get list of available fashion categories
    """
    return [cat.value for cat in FashionCategory]


@router.post("/demo", response_model=ScanResult)
async def load_demo_data():
    """
    Load demo data without specifying a URL
    
    Useful for testing and demonstrations.
    """
    request = ScanRequest(url="https://demo.trendmuse.ai", max_items=25)
    return await scan_website(request)
