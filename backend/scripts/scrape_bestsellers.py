#!/usr/bin/env python3
"""
Best Sellers Scraper for TrendMuse

Scrapes "Best Sellers" / "Top Rated" / "Trending" collections from fashion sites.
Downloads product images for AI design generation.

Usage:
    python scrape_bestsellers.py                  # Scrape all sources
    python scrape_bestsellers.py --download       # Also download images
    python scrape_bestsellers.py --source shein   # Specific source
"""
import asyncio
import argparse
import sys
import os
import aiohttp
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services.scraper import ScraperFactory, SheinScraper, ZaraScraper
from src.services.database import DatabaseService


# Best seller / trending collection URLs
BESTSELLER_SOURCES = {
    # SHEIN - has actual sales data!
    "shein_bestsellers": {
        "url": "https://us.shein.com/bestsellers-Women-Clothing-sc-00891882.html",
        "type": "shein",
        "has_sales_data": True,
        "max_items": 100,
    },
    "shein_trending": {
        "url": "https://us.shein.com/trending/women-clothing-sc-008909160.html",
        "type": "shein",
        "has_sales_data": True,
        "max_items": 100,
    },
    # Zara - curated collections
    "zara_bestsellers": {
        "url": "https://www.zara.com/us/en/woman-best-sellers-l1314.html",
        "type": "zara",
        "has_sales_data": False,
        "max_items": 50,
    },
    # Shopify stores - Best Sellers collections
    "classicwhimsy_bestsellers": {
        "url": "https://classicwhimsy.com/collections/best-sellers",
        "type": "shopify",
        "has_sales_data": False,
        "max_items": 50,
    },
    "jamiekay_bestsellers": {
        "url": "https://jamiekay.com/collections/best-sellers",
        "type": "shopify",
        "has_sales_data": False,
        "max_items": 50,
    },
    "shrimpandgrits_bestsellers": {
        "url": "https://shrimpandgritskids.com/collections/best-sellers",
        "type": "shopify",
        "has_sales_data": False,
        "max_items": 50,
    },
}


async def download_image(session: aiohttp.ClientSession, url: str, save_dir: Path, product_id: str) -> str:
    """Download product image and return local path"""
    if not url:
        return ""
    
    try:
        # Create filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        ext = Path(url.split("?")[0]).suffix or ".jpg"
        filename = f"{product_id}_{url_hash}{ext}"
        filepath = save_dir / filename
        
        if filepath.exists():
            return str(filepath)
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                content = await response.read()
                filepath.write_bytes(content)
                return str(filepath)
    except Exception as e:
        print(f"  [!] Failed to download {url[:50]}...: {e}")
    
    return ""


async def scrape_bestsellers(
    sources: List[str] = None,
    download_images: bool = False,
    db: DatabaseService = None
) -> Dict:
    """Scrape best sellers from configured sources"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "sources_scraped": 0,
        "total_items": 0,
        "items_with_sales": 0,
        "images_downloaded": 0,
        "top_products": [],
    }
    
    # Filter sources
    if sources:
        source_configs = {k: v for k, v in BESTSELLER_SOURCES.items() if k in sources}
    else:
        source_configs = BESTSELLER_SOURCES
    
    # Image download directory
    image_dir = Path(__file__).parent.parent / "data" / "bestseller_images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    async with aiohttp.ClientSession() as http_session:
        for source_name, config in source_configs.items():
            print(f"\n{'='*50}")
            print(f"Scraping: {source_name}")
            print(f"URL: {config['url']}")
            print(f"{'='*50}")
            
            try:
                scraper = ScraperFactory.get_scraper(config["url"])
                items = await scraper.scrape(
                    url=config["url"],
                    max_items=config.get("max_items", 50)
                )
                
                print(f"Found {len(items)} items")
                results["sources_scraped"] += 1
                results["total_items"] += len(items)
                
                for i, item in enumerate(items):
                    # Add position rank (position in bestsellers = popularity indicator)
                    item.trend_score = max(0, 100 - (i * 2))  # Top item = 100, decreasing
                    
                    # Track items with actual sales data
                    if item.sales_count and item.sales_count > 0:
                        results["items_with_sales"] += 1
                    
                    # Download images if requested
                    if download_images and item.image_url:
                        local_path = await download_image(
                            http_session, 
                            item.image_url, 
                            image_dir,
                            item.id
                        )
                        if local_path:
                            results["images_downloaded"] += 1
                            item.local_image_path = local_path
                    
                    # Save to database
                    if db:
                        db.upsert_product(item, source=source_name)
                    
                    # Track top products (first 5 from each source)
                    if i < 5:
                        results["top_products"].append({
                            "source": source_name,
                            "rank": i + 1,
                            "name": item.name,
                            "price": item.price,
                            "sales_count": item.sales_count,
                            "image_url": item.image_url,
                        })
                
            except Exception as e:
                print(f"Error scraping {source_name}: {e}")
                continue
    
    return results


def print_report(results: Dict):
    """Print summary report"""
    print(f"\n{'#'*60}")
    print("BESTSELLERS SCRAPE REPORT")
    print(f"{'#'*60}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Sources scraped: {results['sources_scraped']}")
    print(f"Total items: {results['total_items']}")
    print(f"Items with sales data: {results['items_with_sales']}")
    print(f"Images downloaded: {results['images_downloaded']}")
    
    print(f"\n{'='*60}")
    print("TOP PRODUCTS BY SOURCE")
    print(f"{'='*60}")
    
    current_source = None
    for product in results["top_products"]:
        if product["source"] != current_source:
            current_source = product["source"]
            print(f"\n📦 {current_source}:")
        
        sales_str = f" | {product['sales_count']} sold" if product.get("sales_count") else ""
        print(f"  {product['rank']}. {product['name'][:40]} - ${product['price']}{sales_str}")


async def main():
    parser = argparse.ArgumentParser(description="TrendMuse Best Sellers Scraper")
    parser.add_argument("--source", "-s", action="append", dest="sources", help="Specific source to scrape")
    parser.add_argument("--download", "-d", action="store_true", help="Download product images")
    parser.add_argument("--list", action="store_true", help="List available sources")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available bestseller sources:")
        for name, config in BESTSELLER_SOURCES.items():
            sales = "✓ has sales data" if config.get("has_sales_data") else "✗ no sales data"
            print(f"  {name:30} ({sales})")
        return
    
    # Initialize database
    db_path = Path(__file__).parent.parent / "data" / "trendmuse.db"
    db = DatabaseService(str(db_path))
    
    results = await scrape_bestsellers(
        sources=args.sources,
        download_images=args.download,
        db=db
    )
    
    print_report(results)
    
    # Save results
    import json
    results_path = Path(__file__).parent.parent / "data" / "bestsellers_latest.json"
    
    # Convert datetime for JSON
    results_json = results.copy()
    with open(results_path, "w") as f:
        json.dump(results_json, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
