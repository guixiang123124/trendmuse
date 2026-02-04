#!/usr/bin/env python3
"""
Scheduled Scraping Script for TrendMuse

This script scrapes all configured fashion sites and stores the data in the database.
It can be run manually or scheduled via cron/launchd.

Usage:
    python scheduled_scrape.py                    # Scrape all sources
    python scheduled_scrape.py --source zara     # Scrape specific source
    python scheduled_scrape.py --max-items 300   # Set max items per source
    python scheduled_scrape.py --dry-run         # Test without saving to DB
"""
import asyncio
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services.scraper import (
    ScraperFactory,
    ShopifyScraper,
    ZaraScraper,
    TullabeeScraper,
    LillyPulitzerScraper,
)
from src.services.database import DatabaseService


# All sources to scrape
SCRAPE_SOURCES = {
    # Shopify stores (fast - use JSON API)
    "classicwhimsy.com": {
        "url": "https://classicwhimsy.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "shrimpandgritskids.com": {
        "url": "https://shrimpandgritskids.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "jamiekay.com": {
        "url": "https://jamiekay.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "gigiandmax.com": {
        "url": "https://www.gigiandmax.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "stitchyfish.com": {
        "url": "https://stitchyfish.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "littlebearsmocks.com": {
        "url": "https://littlebearsmocks.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "zuccinikids.com": {
        "url": "https://zuccinikids.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "marienicoleclothing.com": {
        "url": "https://marienicoleclothing.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "morninglavender.com": {
        "url": "https://morninglavender.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    "matildajaneclothing.com": {
        "url": "https://matildajaneclothing.com/collections/all",
        "type": "shopify",
        "max_items": 250,
    },
    # Playwright-based scrapers (slower - browser rendering)
    "zara": {
        "url": "https://www.zara.com/us/en/kids-girl-dresses-l6057.html",
        "type": "zara",
        "max_items": 200,
    },
    "tullabee": {
        "url": "https://tullabee.com/collections/all",
        "type": "tullabee",
        "max_items": 200,
    },
    "lillypulitzer": {
        "url": "https://www.lillypulitzer.com/new-arrivals/",
        "type": "lillypulitzer",
        "max_items": 200,
    },
}


async def scrape_source(source_name: str, config: dict, db: DatabaseService, dry_run: bool = False) -> dict:
    """Scrape a single source and save to database"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scraping: {source_name}")
    print(f"{'='*60}")
    
    result = {
        "source": source_name,
        "status": "pending",
        "items_found": 0,
        "items_saved": 0,
        "price_changes": 0,
        "error": None,
    }
    
    try:
        # Get the appropriate scraper
        scraper = ScraperFactory.get_scraper(config["url"])
        
        # Scrape items
        items = await scraper.scrape(
            url=config["url"],
            max_items=config.get("max_items", 200),
        )
        
        result["items_found"] = len(items)
        print(f"[{source_name}] Found {len(items)} items")
        
        if dry_run:
            print(f"[{source_name}] DRY RUN - not saving to database")
            result["status"] = "dry_run"
            return result
        
        # Save to database
        if items:
            # Create scrape session
            session_id = db.start_scrape_session(source_name, config["url"])
            
            saved_count = 0
            new_count = 0
            
            for item in items:
                # Upsert product (handles price tracking internally)
                product_id, is_new = db.upsert_product(item, source=source_name)
                saved_count += 1
                if is_new:
                    new_count += 1
            
            # Complete session
            db.complete_scrape_session(
                session_id, 
                items_found=len(items), 
                items_new=new_count, 
                items_updated=saved_count - new_count
            )
            
            result["items_saved"] = saved_count
            result["price_changes"] = 0  # Tracked internally by upsert
            result["status"] = "success"
            
            print(f"[{source_name}] Saved {saved_count} items ({new_count} new)")
        else:
            result["status"] = "empty"
            print(f"[{source_name}] No items found")
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"[{source_name}] ERROR: {e}")
    
    return result


async def run_scheduled_scrape(
    sources: list = None,
    max_items: int = None,
    dry_run: bool = False,
    shopify_only: bool = False,
    playwright_only: bool = False,
):
    """Run the scheduled scrape for all or selected sources"""
    print(f"\n{'#'*60}")
    print(f"# TrendMuse Scheduled Scrape")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    # Initialize database
    db_path = Path(__file__).parent.parent / "data" / "trendmuse.db"
    db = DatabaseService(str(db_path))
    
    # Filter sources
    if sources:
        source_configs = {k: v for k, v in SCRAPE_SOURCES.items() if k in sources}
    else:
        source_configs = SCRAPE_SOURCES.copy()
    
    if shopify_only:
        source_configs = {k: v for k, v in source_configs.items() if v["type"] == "shopify"}
    elif playwright_only:
        source_configs = {k: v for k, v in source_configs.items() if v["type"] != "shopify"}
    
    # Override max_items if specified
    if max_items:
        for config in source_configs.values():
            config["max_items"] = max_items
    
    print(f"\nSources to scrape: {len(source_configs)}")
    print(f"Sources: {', '.join(source_configs.keys())}")
    
    results = []
    
    # Scrape Shopify stores first (faster)
    shopify_sources = {k: v for k, v in source_configs.items() if v["type"] == "shopify"}
    for name, config in shopify_sources.items():
        result = await scrape_source(name, config, db, dry_run)
        results.append(result)
    
    # Then scrape Playwright sources (slower)
    playwright_sources = {k: v for k, v in source_configs.items() if v["type"] != "shopify"}
    for name, config in playwright_sources.items():
        result = await scrape_source(name, config, db, dry_run)
        results.append(result)
    
    # Print summary
    print(f"\n{'='*60}")
    print("SCRAPE SUMMARY")
    print(f"{'='*60}")
    
    total_found = sum(r["items_found"] for r in results)
    total_saved = sum(r["items_saved"] for r in results)
    total_price_changes = sum(r["price_changes"] for r in results)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    
    print(f"Sources scraped: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total items found: {total_found}")
    print(f"Total items saved: {total_saved}")
    print(f"Price changes detected: {total_price_changes}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print errors if any
    errors = [r for r in results if r["status"] == "error"]
    if errors:
        print(f"\n{'='*60}")
        print("ERRORS")
        print(f"{'='*60}")
        for r in errors:
            print(f"  {r['source']}: {r['error']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="TrendMuse Scheduled Scraper")
    parser.add_argument(
        "--source", "-s",
        type=str,
        action="append",
        dest="sources",
        help="Specific source to scrape (can be repeated)",
    )
    parser.add_argument(
        "--max-items", "-m",
        type=int,
        default=None,
        help="Maximum items per source",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test scraping without saving to database",
    )
    parser.add_argument(
        "--shopify-only",
        action="store_true",
        help="Only scrape Shopify stores (faster)",
    )
    parser.add_argument(
        "--playwright-only",
        action="store_true",
        help="Only scrape Playwright-based sources",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available sources",
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available sources:")
        for name, config in SCRAPE_SOURCES.items():
            print(f"  {name:25} ({config['type']:10}) - {config['url']}")
        return
    
    asyncio.run(run_scheduled_scrape(
        sources=args.sources,
        max_items=args.max_items,
        dry_run=args.dry_run,
        shopify_only=args.shopify_only,
        playwright_only=args.playwright_only,
    ))


if __name__ == "__main__":
    main()
