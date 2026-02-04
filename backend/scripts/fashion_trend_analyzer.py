#!/usr/bin/env python3
"""
Fashion Trend Analyzer - TrendMuse

Analyzes popular fashion blogs and publications to identify:
- Trending styles and keywords
- Seasonal color palettes
- Popular silhouettes and patterns
- Emerging designers and brands

Sources:
- Vogue, Elle, Harper's Bazaar
- Who What Wear, Refinery29
- The Zoe Report, Fashionista
- Kids fashion: Mini Magazine, Babiekins
"""
import asyncio
import aiohttp
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

# Fashion blog sources
FASHION_SOURCES = {
    # Major fashion publications
    "vogue_trends": {
        "url": "https://www.vogue.com/fashion/trends",
        "type": "publication",
        "category": "high_fashion",
    },
    "elle_trends": {
        "url": "https://www.elle.com/fashion/trend-reports/",
        "type": "publication",
        "category": "high_fashion",
    },
    "whowhatwear": {
        "url": "https://www.whowhatwear.com/fashion/trends",
        "type": "blog",
        "category": "mainstream",
    },
    "refinery29_fashion": {
        "url": "https://www.refinery29.com/en-us/fashion",
        "type": "blog",
        "category": "mainstream",
    },
    "fashionista": {
        "url": "https://fashionista.com/tag/trends",
        "type": "blog",
        "category": "industry",
    },
    # Kids fashion
    "minimagazine": {
        "url": "https://minimagazine.com/",
        "type": "blog",
        "category": "kids",
    },
}

# Fashion keyword categories for extraction
FASHION_KEYWORDS = {
    "silhouettes": [
        "a-line", "shift", "maxi", "midi", "mini", "bodycon", "oversized",
        "fitted", "flowy", "structured", "relaxed", "tailored", "boxy",
        "balloon", "puff sleeve", "bishop sleeve", "flutter", "tiered",
        "smocked", "empire waist", "drop waist", "high-waisted"
    ],
    "patterns": [
        "floral", "stripe", "striped", "plaid", "gingham", "polka dot",
        "animal print", "leopard", "zebra", "geometric", "abstract",
        "paisley", "toile", "botanical", "tropical", "ditsy", "watercolor",
        "tie-dye", "ombre", "color block", "checkered"
    ],
    "colors": [
        "pink", "blue", "green", "yellow", "red", "orange", "purple",
        "lavender", "coral", "mint", "sage", "terracotta", "burgundy",
        "navy", "cream", "ivory", "blush", "rose", "dusty", "muted",
        "pastel", "neon", "bright", "neutral", "earthy", "jewel tone"
    ],
    "fabrics": [
        "cotton", "linen", "silk", "satin", "velvet", "denim", "leather",
        "tweed", "knit", "jersey", "chiffon", "organza", "tulle", "lace",
        "eyelet", "broderie", "crochet", "mesh", "sequin", "metallic"
    ],
    "styles": [
        "boho", "bohemian", "preppy", "classic", "minimalist", "maximalist",
        "romantic", "edgy", "sporty", "athleisure", "coastal", "cottagecore",
        "quiet luxury", "old money", "coquette", "mob wife", "clean girl",
        "coastal grandmother", "barbiecore", "balletcore"
    ],
    "details": [
        "ruffle", "bow", "button", "embroidered", "beaded", "fringe",
        "pleated", "gathered", "shirred", "smocked", "quilted", "cutout",
        "asymmetric", "wrap", "tie", "belted", "collar", "peter pan"
    ],
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch page content"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"  [!] Failed to fetch {url}: {e}")
    return None


def extract_article_text(html: str) -> str:
    """Extract main article text from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script, style, nav elements
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    # Get text from article or main content
    article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|article|post'))
    
    if article:
        text = article.get_text(separator=' ', strip=True)
    else:
        text = soup.get_text(separator=' ', strip=True)
    
    return text.lower()


def extract_headlines(html: str) -> List[str]:
    """Extract article headlines/titles"""
    soup = BeautifulSoup(html, 'html.parser')
    headlines = []
    
    # Find headline elements
    for tag in soup.find_all(['h1', 'h2', 'h3', 'a']):
        text = tag.get_text(strip=True)
        # Filter for fashion-related headlines
        if len(text) > 20 and len(text) < 200:
            text_lower = text.lower()
            fashion_words = ['trend', 'style', 'fashion', 'wear', 'outfit', 'dress', 'spring', 'summer', 'fall', 'winter', '2026', '2025']
            if any(word in text_lower for word in fashion_words):
                headlines.append(text)
    
    return headlines[:20]  # Limit to top 20


def extract_fashion_keywords(text: str) -> Dict[str, Counter]:
    """Extract fashion keywords by category"""
    results = {}
    
    for category, keywords in FASHION_KEYWORDS.items():
        counter = Counter()
        for keyword in keywords:
            # Count occurrences (word boundary matching)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            count = len(re.findall(pattern, text, re.IGNORECASE))
            if count > 0:
                counter[keyword] = count
        results[category] = counter
    
    return results


async def analyze_source(session: aiohttp.ClientSession, name: str, config: dict) -> dict:
    """Analyze a single fashion source"""
    print(f"\n  Analyzing: {name}")
    
    result = {
        "source": name,
        "url": config["url"],
        "category": config.get("category", "general"),
        "scraped_at": datetime.now().isoformat(),
        "headlines": [],
        "keywords": {},
        "top_trends": [],
    }
    
    html = await fetch_page(session, config["url"])
    if not html:
        result["error"] = "Failed to fetch"
        return result
    
    # Extract headlines
    result["headlines"] = extract_headlines(html)
    print(f"    Found {len(result['headlines'])} headlines")
    
    # Extract text and keywords
    text = extract_article_text(html)
    keyword_counts = extract_fashion_keywords(text)
    
    # Convert counters to dicts for JSON
    result["keywords"] = {k: dict(v.most_common(10)) for k, v in keyword_counts.items()}
    
    # Identify top trends (most mentioned keywords across categories)
    all_keywords = Counter()
    for category_counts in keyword_counts.values():
        all_keywords.update(category_counts)
    
    result["top_trends"] = [{"keyword": k, "count": c} for k, c in all_keywords.most_common(15)]
    print(f"    Top keywords: {', '.join([t['keyword'] for t in result['top_trends'][:5]])}")
    
    return result


async def analyze_all_sources(sources: List[str] = None) -> dict:
    """Analyze all fashion sources"""
    print(f"\n{'='*60}")
    print("FASHION TREND ANALYSIS")
    print(f"{'='*60}")
    
    if sources:
        source_configs = {k: v for k, v in FASHION_SOURCES.items() if k in sources}
    else:
        source_configs = FASHION_SOURCES
    
    results = {
        "analyzed_at": datetime.now().isoformat(),
        "sources": [],
        "aggregate_trends": {},
        "trend_summary": {},
    }
    
    async with aiohttp.ClientSession() as session:
        for name, config in source_configs.items():
            source_result = await analyze_source(session, name, config)
            results["sources"].append(source_result)
            await asyncio.sleep(1)  # Rate limiting
    
    # Aggregate trends across all sources
    aggregate = {category: Counter() for category in FASHION_KEYWORDS.keys()}
    
    for source in results["sources"]:
        if "keywords" in source:
            for category, keywords in source["keywords"].items():
                aggregate[category].update(keywords)
    
    results["aggregate_trends"] = {
        k: [{"keyword": kw, "count": c} for kw, c in v.most_common(15)]
        for k, v in aggregate.items()
    }
    
    # Generate trend summary
    results["trend_summary"] = generate_trend_summary(aggregate)
    
    return results


def generate_trend_summary(aggregate: Dict[str, Counter]) -> dict:
    """Generate human-readable trend summary"""
    summary = {
        "top_silhouettes": [k for k, _ in aggregate["silhouettes"].most_common(5)],
        "top_patterns": [k for k, _ in aggregate["patterns"].most_common(5)],
        "top_colors": [k for k, _ in aggregate["colors"].most_common(5)],
        "top_fabrics": [k for k, _ in aggregate["fabrics"].most_common(5)],
        "top_styles": [k for k, _ in aggregate["styles"].most_common(5)],
        "top_details": [k for k, _ in aggregate["details"].most_common(5)],
    }
    return summary


def print_report(results: dict):
    """Print trend analysis report"""
    print(f"\n{'#'*60}")
    print("FASHION TREND REPORT")
    print(f"Date: {results['analyzed_at'][:10]}")
    print(f"{'#'*60}")
    
    summary = results.get("trend_summary", {})
    
    print("\n📊 TOP TRENDS BY CATEGORY\n")
    
    categories = [
        ("👗 Silhouettes", "top_silhouettes"),
        ("🎨 Patterns", "top_patterns"),
        ("🌈 Colors", "top_colors"),
        ("🧵 Fabrics", "top_fabrics"),
        ("✨ Styles", "top_styles"),
        ("🎀 Details", "top_details"),
    ]
    
    for label, key in categories:
        trends = summary.get(key, [])
        if trends:
            print(f"{label}: {', '.join(trends)}")
    
    print("\n📰 HEADLINES\n")
    for source in results.get("sources", []):
        if source.get("headlines"):
            print(f"\n{source['source']}:")
            for headline in source["headlines"][:3]:
                print(f"  • {headline[:80]}...")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fashion Trend Analyzer")
    parser.add_argument("--source", "-s", action="append", dest="sources")
    parser.add_argument("--list", action="store_true", help="List sources")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available fashion sources:")
        for name, config in FASHION_SOURCES.items():
            print(f"  {name:25} ({config['category']:12}) - {config['url']}")
        return
    
    results = await analyze_all_sources(args.sources)
    print_report(results)
    
    # Save results
    output_path = args.output or Path(__file__).parent.parent / "data" / "fashion_trends_latest.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
