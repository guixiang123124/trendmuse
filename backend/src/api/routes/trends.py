"""
Trends API Routes

Provides endpoints for trend analysis and database statistics.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime
from collections import Counter
import re

from src.services.database import get_database

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/stats")
async def get_stats():
    """Get overall database statistics"""
    db = get_database()
    return db.get_stats()


@router.get("/products")
async def get_products(
    source: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    Query products from database with filters.
    
    - **source**: Filter by source website (e.g., 'classicwhimsy.com')
    - **category**: Filter by category (e.g., 'dress', 'top')
    - **brand**: Filter by brand name
    - **min_price**: Minimum price
    - **max_price**: Maximum price
    - **limit**: Max results (default 50, max 200)
    - **offset**: Pagination offset
    """
    db = get_database()
    products = db.get_products(
        source=source,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset
    )
    
    total = db.get_product_count(source=source)
    
    return {
        "products": products,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/sources")
async def get_sources():
    """Get list of all scraped sources with product counts"""
    db = get_database()
    stats = db.get_stats()
    
    sources = []
    for source, count in stats.get('by_source', {}).items():
        sources.append({
            "name": source,
            "display_name": source.replace('.com', '').replace('www.', '').title(),
            "product_count": count
        })
    
    return {"sources": sorted(sources, key=lambda x: x['product_count'], reverse=True)}


@router.get("/categories")
async def get_categories():
    """Get list of all categories with product counts"""
    db = get_database()
    stats = db.get_stats()
    
    categories = []
    for category, count in stats.get('by_category', {}).items():
        categories.append({
            "name": category,
            "display_name": category.title(),
            "product_count": count
        })
    
    return {"categories": sorted(categories, key=lambda x: x['product_count'], reverse=True)}


@router.get("/price-distribution")
async def get_price_distribution(source: Optional[str] = None):
    """Get price distribution data for charts"""
    db = get_database()
    products = db.get_products(source=source, limit=1000)
    
    if not products:
        return {"distribution": [], "stats": {}}
    
    prices = [p['price'] for p in products if p.get('price')]
    
    if not prices:
        return {"distribution": [], "stats": {}}
    
    # Calculate price ranges
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    
    # Create distribution buckets
    buckets = []
    ranges = [
        (0, 20, "$0-20"),
        (20, 40, "$20-40"),
        (40, 60, "$40-60"),
        (60, 80, "$60-80"),
        (80, 100, "$80-100"),
        (100, float('inf'), "$100+")
    ]
    
    for low, high, label in ranges:
        count = len([p for p in prices if low <= p < high])
        buckets.append({"range": label, "count": count})
    
    return {
        "distribution": buckets,
        "stats": {
            "min": round(min_price, 2),
            "max": round(max_price, 2),
            "avg": round(avg_price, 2),
            "total": len(prices)
        }
    }


@router.get("/top-colors")
async def get_top_colors(source: Optional[str] = None, limit: int = 10):
    """Get most common colors across products"""
    db = get_database()
    products = db.get_products(source=source, limit=500)
    
    color_counts = {}
    for product in products:
        colors = product.get('colors', [])
        if isinstance(colors, str):
            import json
            try:
                colors = json.loads(colors)
            except:
                colors = []
        for color in colors:
            color_counts[color] = color_counts.get(color, 0) + 1
    
    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return {
        "colors": [{"name": c[0], "count": c[1]} for c in sorted_colors]
    }


@router.get("/top-tags")
async def get_top_tags(source: Optional[str] = None, limit: int = 20):
    """Get most common tags across products"""
    db = get_database()
    products = db.get_products(source=source, limit=500)
    
    tag_counts = {}
    for product in products:
        tags = product.get('tags', [])
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except:
                tags = []
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return {
        "tags": [{"name": t[0], "count": t[1]} for t in sorted_tags]
    }


@router.get("/recent-sessions")
async def get_recent_sessions(limit: int = 10):
    """Get recent scrape sessions"""
    db = get_database()
    sessions = db.get_recent_sessions(limit=limit)
    return {"sessions": sessions}


@router.post("/calculate")
async def calculate_trends(period: str = "weekly"):
    """
    Calculate and store trend data.
    
    - **period**: 'daily', 'weekly', or 'monthly'
    """
    if period not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Invalid period. Use: daily, weekly, monthly")
    
    db = get_database()
    result = db.calculate_trends(period=period)
    return result


@router.get("/summary")
async def get_trend_summary():
    """Get a comprehensive trend summary for the dashboard"""
    db = get_database()
    stats = db.get_stats()
    
    # Get products for analysis
    products = db.get_products(limit=500)
    
    # Calculate insights
    prices = [p['price'] for p in products if p.get('price')]
    
    # Top brands by product count
    brand_counts = {}
    for p in products:
        brand = p.get('brand', 'Unknown')
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
    top_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Products on sale
    on_sale = len([p for p in products if p.get('original_price') and p.get('price') and p['price'] < p['original_price']])
    
    return {
        "overview": {
            "total_products": stats['total_products'],
            "total_sources": len(stats.get('by_source', {})),
            "total_categories": len(stats.get('by_category', {})),
            "updated_today": stats.get('updated_today', 0),
            "new_today": stats.get('new_today', 0),
        },
        "pricing": {
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "on_sale_count": on_sale,
        },
        "top_brands": [{"name": b[0], "count": b[1]} for b in top_brands],
        "by_source": stats.get('by_source', {}),
        "by_category": stats.get('by_category', {}),
    }


@router.get("/products-by-brand")
async def get_products_grouped_by_brand(
    items_per_brand: int = Query(default=10, le=30, description="Number of items per brand"),
    include_sources: Optional[str] = Query(None, description="Comma-separated source filter")
):
    """
    Get products grouped by brand/source, useful for displaying trending items
    from multiple brands at once.
    
    Returns up to `items_per_brand` products from each scraped source.
    """
    db = get_database()
    stats = db.get_stats()
    
    sources = list(stats.get('by_source', {}).keys())
    
    # Filter sources if specified
    if include_sources:
        filter_list = [s.strip() for s in include_sources.split(',')]
        sources = [s for s in sources if s in filter_list]
    
    result = {}
    for source in sources:
        products = db.get_products(source=source, limit=items_per_brand)
        if products:
            result[source] = {
                "brand_name": source.replace('.com', '').replace('www.', '').title(),
                "total_count": stats['by_source'].get(source, 0),
                "products": products
            }
    
    return {
        "brands": result,
        "total_brands": len(result),
        "items_per_brand": items_per_brand
    }


@router.get("/analytics")
async def get_trend_analytics():
    """
    Get comprehensive trend analytics with semantic analysis.
    
    Includes:
    - Trending themes/topics extracted from product names and tags
    - Style patterns
    - Price trends
    - Category breakdown
    - Color palettes
    """
    db = get_database()
    products = db.get_products(limit=1000)
    
    if not products:
        return {"error": "No products in database"}
    
    # Extract keywords from product names for theme analysis
    all_words = []
    all_tags = []
    category_products = {}
    source_stats = {}
    
    for p in products:
        # Extract words from name
        name = p.get('name', '')
        words = re.findall(r'\b[a-zA-Z]{3,}\b', name.lower())
        all_words.extend(words)
        
        # Collect tags
        tags = p.get('tags', [])
        if isinstance(tags, list):
            all_tags.extend([t.lower() for t in tags])
        
        # Group by category
        cat = p.get('category', 'other')
        if cat not in category_products:
            category_products[cat] = []
        category_products[cat].append(p)
        
        # Source stats
        source = p.get('source', 'unknown')
        if source not in source_stats:
            source_stats[source] = {'count': 0, 'prices': [], 'categories': []}
        source_stats[source]['count'] += 1
        if p.get('price'):
            source_stats[source]['prices'].append(p['price'])
        source_stats[source]['categories'].append(cat)
    
    # Common stopwords to filter
    stopwords = {'the', 'and', 'for', 'with', 'set', 'top', 'new', 'kids', 'baby', 
                 'girls', 'boys', 'little', 'size', 'one', 'two', 'all', 'cotton'}
    
    # Calculate trending themes
    word_counts = Counter([w for w in all_words if w not in stopwords])
    trending_themes = [{"theme": w, "count": c} for w, c in word_counts.most_common(20)]
    
    # Calculate trending tags
    tag_counts = Counter(all_tags)
    trending_tags = [{"tag": t, "count": c} for t, c in tag_counts.most_common(15)]
    
    # Calculate category insights
    category_insights = []
    for cat, prods in category_products.items():
        prices = [p['price'] for p in prods if p.get('price')]
        category_insights.append({
            "category": cat,
            "product_count": len(prods),
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0
            }
        })
    category_insights.sort(key=lambda x: x['product_count'], reverse=True)
    
    # Brand/source insights
    brand_insights = []
    for source, data in source_stats.items():
        prices = data['prices']
        cat_counts = Counter(data['categories'])
        top_category = cat_counts.most_common(1)[0][0] if cat_counts else 'unknown'
        
        brand_insights.append({
            "brand": source.replace('.com', '').replace('www.', '').title(),
            "source": source,
            "product_count": data['count'],
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "top_category": top_category,
            "specialty": top_category
        })
    brand_insights.sort(key=lambda x: x['product_count'], reverse=True)
    
    # Overall price distribution
    all_prices = [p['price'] for p in products if p.get('price')]
    price_brackets = {
        "budget": len([p for p in all_prices if p < 30]),
        "mid_range": len([p for p in all_prices if 30 <= p < 60]),
        "premium": len([p for p in all_prices if 60 <= p < 100]),
        "luxury": len([p for p in all_prices if p >= 100])
    }
    
    return {
        "summary": {
            "total_products": len(products),
            "total_brands": len(source_stats),
            "total_categories": len(category_products),
            "avg_price": round(sum(all_prices) / len(all_prices), 2) if all_prices else 0
        },
        "trending_themes": trending_themes,
        "trending_tags": trending_tags,
        "category_insights": category_insights,
        "brand_insights": brand_insights,
        "price_distribution": price_brackets,
        "insights": {
            "top_theme": trending_themes[0]['theme'] if trending_themes else None,
            "most_popular_category": category_insights[0]['category'] if category_insights else None,
            "price_trend": "mid-range focus" if price_brackets.get('mid_range', 0) > price_brackets.get('premium', 0) else "premium focus"
        }
    }
