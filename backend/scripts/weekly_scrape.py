#!/usr/bin/env python3
"""
Weekly Scrape Script for TrendMuse

Runs weekly to fetch latest products from all configured Shopify stores.
Can be run manually or via cron job.

Usage:
    python scripts/weekly_scrape.py [--max-items 200]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.scraper import ShopifyScraper
from src.services.database import get_database


# Configured Shopify stores to scrape
SHOPIFY_STORES = [
    ("https://classicwhimsy.com/collections/all", "classicwhimsy.com", "Classic Whimsy"),
    ("https://shrimpandgritskids.com/collections/all", "shrimpandgritskids.com", "Shrimp & Grits Kids"),
    ("https://jamiekay.com/collections/all", "jamiekay.com", "Jamie Kay"),
    ("https://www.gigiandmax.com/collections/all", "gigiandmax.com", "Gigi and Max"),
    ("https://www.stitchyfish.com/collections/all", "stitchyfish.com", "Stitchy Fish"),
    ("https://littlebearsmocks.com/collections/all", "littlebearsmocks.com", "Little Bear Smocks"),
    ("https://www.zuccinikids.com/collections/all", "zuccinikids.com", "Zuccini Kids"),
    ("https://morninglavender.com/collections/all", "morninglavender.com", "Morning Lavender"),
    ("https://matildajaneclothing.com/collections/all", "matildajaneclothing.com", "Matilda Jane"),
]


async def run_weekly_scrape(max_items: int = 200, verbose: bool = True):
    """
    Run the weekly scrape for all configured stores.
    
    Args:
        max_items: Maximum items to fetch per store
        verbose: Print progress updates
    """
    scraper = ShopifyScraper()
    db = get_database()
    
    total_stats = {
        'sites_success': 0,
        'sites_failed': 0,
        'products_total': 0,
        'products_new': 0,
        'products_updated': 0,
    }
    
    start_time = datetime.now()
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"TrendMuse Weekly Scrape - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Stores: {len(SHOPIFY_STORES)} | Max items per store: {max_items}")
        print(f"{'='*60}\n")
    
    for url, source, name in SHOPIFY_STORES:
        if verbose:
            print(f"📦 Scraping {name}...", end=" ", flush=True)
        
        session_id = db.start_scrape_session(source, url)
        
        try:
            items = await scraper.scrape(url, max_items=max_items)
            
            if items:
                stats = db.bulk_upsert_products(items, source)
                db.complete_scrape_session(
                    session_id, 
                    stats['total'], 
                    stats['new'], 
                    stats['updated']
                )
                
                total_stats['sites_success'] += 1
                total_stats['products_total'] += stats['total']
                total_stats['products_new'] += stats['new']
                total_stats['products_updated'] += stats['updated']
                
                if verbose:
                    print(f"✅ {stats['total']} items ({stats['new']} new, {stats['updated']} updated)")
            else:
                db.complete_scrape_session(session_id, 0, 0, 0, "No items found")
                total_stats['sites_failed'] += 1
                if verbose:
                    print("⚠️ No items found")
                    
        except Exception as e:
            db.complete_scrape_session(session_id, 0, 0, 0, str(e))
            total_stats['sites_failed'] += 1
            if verbose:
                print(f"❌ Error: {str(e)[:50]}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if verbose:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Sites: {total_stats['sites_success']} success, {total_stats['sites_failed']} failed")
        print(f"Products: {total_stats['products_total']} total")
        print(f"  - New: {total_stats['products_new']}")
        print(f"  - Updated: {total_stats['products_updated']}")
        print(f"{'='*60}\n")
        
        # Database stats
        db_stats = db.get_stats()
        print(f"Database total: {db_stats['total_products']} products")
    
    return total_stats


def main():
    parser = argparse.ArgumentParser(description="TrendMuse Weekly Scraper")
    parser.add_argument(
        "--max-items", 
        type=int, 
        default=200,
        help="Maximum items to fetch per store (default: 200)"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Suppress output"
    )
    args = parser.parse_args()
    
    stats = asyncio.run(run_weekly_scrape(
        max_items=args.max_items,
        verbose=not args.quiet
    ))
    
    # Exit with error code if all sites failed
    if stats['sites_success'] == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
