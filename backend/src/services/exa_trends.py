"""
Exa Trend Data Pipeline

Uses Exa semantic search (via mcporter) to discover real-time fashion trends
from across the web. Replaces/supplements the hardcoded trend data in discovery.py.
"""
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# Exa search queries for fashion trends
TREND_QUERIES = [
    {
        "query": "trending fashion products 2026 spring summer",
        "category": "seasonal_trends",
    },
    {
        "query": "best selling Shopify fashion brands 2025 2026",
        "category": "brand_discovery",
    },
    {
        "query": "viral fashion TikTok products trending now",
        "category": "viral_products",
    },
    {
        "query": "fashion trend forecast spring summer 2026",
        "category": "trend_forecast",
    },
    {
        "query": "most popular women's clothing styles right now",
        "category": "popular_styles",
    },
    {
        "query": "emerging fashion aesthetic trends 2025 2026",
        "category": "aesthetic_trends",
    },
]


def _call_exa(query: str, num_results: int = 5, max_chars: int = 3000) -> Optional[Dict]:
    """Call Exa web_search_exa via mcporter CLI using positional args."""
    try:
        # mcporter positional args: key:"value" format
        args = [
            "mcporter", "call", "exa.web_search_exa",
            f'query:{query}',
            f'numResults:{num_results}',
            f'contextMaxCharacters:{max_chars}',
        ]
        result = subprocess.run(
            args,
            capture_output=True, text=True, timeout=45,
            env={
                **subprocess.os.environ,
                "PATH": "/opt/homebrew/bin:" + subprocess.os.environ.get("PATH", ""),
                "MCPORTER_CONFIG": subprocess.os.environ.get(
                    "MCPORTER_CONFIG",
                    str(Path.home() / ".openclaw/workspace/config/mcporter.json")
                ),
            },
        )
        if result.returncode != 0:
            print(f"[ExaTrends] mcporter error: {result.stderr[:200]}")
            return None
        
        output = result.stdout.strip()
        if not output:
            return None
        
        # mcporter returns text content directly
        return {"text": output}
    except subprocess.TimeoutExpired:
        print(f"[ExaTrends] Timeout for query: {query}")
        return None
    except FileNotFoundError:
        print("[ExaTrends] mcporter not found in PATH")
        return None
    except Exception as e:
        print(f"[ExaTrends] Error: {e}")
        return None


def _parse_trend_results(raw_results: Dict, category: str) -> List[Dict]:
    """Parse Exa results into structured trend items."""
    items = []
    
    text = raw_results.get("text", "")
    if not text and isinstance(raw_results, dict):
        # Try to extract content from nested structure
        for key in ["content", "results", "data"]:
            if key in raw_results:
                val = raw_results[key]
                if isinstance(val, str):
                    text = val
                elif isinstance(val, list):
                    text = "\n".join(str(v) for v in val)
                break
    
    if not text:
        text = json.dumps(raw_results) if raw_results else ""
    
    fashion_keywords = [
        "trending", "viral", "popular", "best-selling", "bestseller",
        "hot", "rising", "emerging", "must-have", "breakout",
    ]
    
    fashion_terms = [
        "dress", "skirt", "pants", "jeans", "top", "blouse", "jacket",
        "coat", "blazer", "cardigan", "sweater", "hoodie", "shoes",
        "boots", "sneakers", "bag", "accessories", "earrings", "necklace",
        "aesthetic", "style", "fashion", "trend", "outfit", "look",
        "linen", "denim", "silk", "satin", "cotton", "leather",
        "minimalist", "streetwear", "vintage", "boho", "coquette",
        "wide-leg", "oversized", "midi", "maxi", "corset", "mesh",
    ]
    
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if len(line) < 10 or len(line) > 200:
            continue
        
        # Skip metadata lines
        lower = line.lower()
        if any(skip in lower for skip in ["published:", "url:", "http", "cookie", "privacy", "©", "sign up", "log in", "title:"]):
            continue
        
        # Score the line for fashion relevance
        score = 0
        for kw in fashion_keywords:
            if kw in lower:
                score += 10
        for term in fashion_terms:
            if term in lower:
                score += 5
        
        if score >= 10:
            # Clean up the line
            name = re.sub(r'[\*\#\[\]\(\)\|]', '', line).strip()
            name = re.sub(r'^[-\d\.\s:>]+', '', name).strip()
            # Remove "Title:" prefix
            name = re.sub(r'^Title:\s*', '', name).strip()
            if 8 < len(name) < 120:
                direction = "hot" if score >= 25 else "rising" if score >= 15 else "stable"
                items.append({
                    "name": name,
                    "score": min(95, 45 + score),
                    "direction": direction,
                    "description": f"Discovered via Exa ({category})",
                    "source": "exa",
                    "category": category,
                    "discovered_at": datetime.now().isoformat(),
                })
    
    return items[:10]


def fetch_exa_trends(queries: List[Dict] = None) -> Dict[str, Any]:
    """
    Fetch trends from Exa for all configured queries.
    
    Returns structured trend data organized by category.
    """
    if queries is None:
        queries = TREND_QUERIES
    
    all_trends = []
    raw_data = {}
    errors = []
    
    for q in queries:
        query_text = q["query"]
        category = q["category"]
        
        print(f"[ExaTrends] Searching: {query_text}")
        result = _call_exa(query_text, num_results=5)
        
        if result:
            raw_data[category] = result
            parsed = _parse_trend_results(result, category)
            all_trends.extend(parsed)
            print(f"[ExaTrends]   Found {len(parsed)} trend items")
        else:
            errors.append(f"Failed: {query_text}")
    
    # Deduplicate by name similarity
    seen_names = set()
    unique_trends = []
    for t in all_trends:
        name_key = t["name"].lower()[:30]
        if name_key not in seen_names:
            seen_names.add(name_key)
            unique_trends.append(t)
    
    # Sort by score
    unique_trends.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "source": "Exa Semantic Search",
        "updated_at": datetime.now().isoformat(),
        "total_trends": len(unique_trends),
        "trends": unique_trends[:50],
        "categories_searched": [q["category"] for q in queries],
        "errors": errors,
        "raw_results_available": bool(raw_data),
    }


def fetch_shopify_brands() -> List[Dict]:
    """
    Use Exa to discover trending Shopify fashion brands.
    Returns list of brand info with store URLs.
    """
    result = _call_exa(
        "best new Shopify fashion stores 2025 2026 trending brands",
        num_results=8,
        max_chars=5000,
    )
    
    if not result:
        return []
    
    brands = []
    text = result.get("text", json.dumps(result))
    
    # Extract URLs that look like Shopify stores
    urls = re.findall(r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|co|shop|store))', text)
    
    for url_domain in set(urls):
        brand_name = url_domain.split('.')[0].replace('-', ' ').title()
        brands.append({
            "name": brand_name,
            "domain": url_domain,
            "url": f"https://{url_domain}",
            "source": "exa_discovery",
            "discovered_at": datetime.now().isoformat(),
        })
    
    return brands


# Cache for trend results (in-memory, refreshed on demand)
_cached_trends: Optional[Dict] = None
_cache_time: Optional[datetime] = None
CACHE_TTL_MINUTES = 60


def get_cached_trends(force_refresh: bool = False) -> Dict[str, Any]:
    """Get trends with simple in-memory caching."""
    global _cached_trends, _cache_time
    
    if (
        not force_refresh
        and _cached_trends is not None
        and _cache_time is not None
        and (datetime.now() - _cache_time).total_seconds() < CACHE_TTL_MINUTES * 60
    ):
        return _cached_trends
    
    _cached_trends = fetch_exa_trends()
    _cache_time = datetime.now()
    return _cached_trends
