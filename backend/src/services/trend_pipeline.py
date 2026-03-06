"""
TrendMuse Real-Time Trend Data Pipeline

Sources:
1. Exa Semantic Search — fashion trends, viral products, bestsellers
2. Scrapling — direct Shopify/fashion site scraping (bypasses Cloudflare)
3. Agent Reach (xreach) — Twitter/X fashion KOL tracking
4. Google Trends — search volume signals

Pipeline: Discover → Scrape → Analyze → Store → Serve
"""

import json
import subprocess
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "trendmuse.db"


def init_trend_tables():
    """Create trend-specific tables if they don't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Trend signals from various sources
    c.execute("""
        CREATE TABLE IF NOT EXISTS trend_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,           -- exa, scrapling, xreach, google_trends
            signal_type TEXT NOT NULL,       -- product, article, social_post, search_trend
            title TEXT,
            url TEXT,
            content TEXT,                   -- extracted text/description
            image_url TEXT,
            brand TEXT,
            category TEXT,                  -- tops, bottoms, outerwear, accessories, etc.
            price REAL,
            currency TEXT DEFAULT 'USD',
            trend_score REAL DEFAULT 0,     -- 0-100 composite score
            raw_data TEXT,                  -- JSON blob of original data
            content_hash TEXT UNIQUE,       -- dedup key
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Aggregated trend categories
    c.execute("""
        CREATE TABLE IF NOT EXISTS trend_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,             -- e.g., "oversized blazers", "pastel pink"
            category_type TEXT,             -- style, color, material, silhouette
            signal_count INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            peak_score REAL DEFAULT 0,
            status TEXT DEFAULT 'rising',   -- rising, peaked, declining, stable
            sources TEXT,                   -- JSON array of contributing sources
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Trend snapshots for time-series
    c.execute("""
        CREATE TABLE IF NOT EXISTS trend_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER REFERENCES trend_categories(id),
            score REAL,
            signal_count INTEGER,
            snapshot_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Index for fast queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_signals_source ON trend_signals(source)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_signals_category ON trend_signals(category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_signals_discovered ON trend_signals(discovered_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_categories_status ON trend_categories(status)")
    
    conn.commit()
    conn.close()
    print(f"✅ Trend tables initialized at {DB_PATH}")


def _content_hash(text: str) -> str:
    """Generate dedup hash from content."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _run_mcporter(tool: str, **kwargs) -> Optional[str]:
    """Call mcporter tool and return stdout."""
    args_str = ", ".join(f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {v}' for k, v in kwargs.items())
    cmd = f'mcporter call \'{tool}({args_str})\''
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        print(f"⚠️ mcporter timeout: {tool}")
        return None


def _run_agent_reach(channel: str, method: str, **kwargs) -> Optional[str]:
    """Call Agent Reach CLI."""
    args = " ".join(f'--{k} "{v}"' for k, v in kwargs.items())
    cmd = f'~/.agent-reach-venv/bin/agent-reach {channel} {method} {args}'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        return None


# ============================================================
# Source 1: Exa Semantic Search
# ============================================================

EXA_QUERIES = [
    "trending fashion products bestsellers 2026",
    "viral fashion TikTok products trending now",
    "best selling Shopify fashion brands spring 2026",
    "fashion trend forecast spring summer 2026 colors styles",
    "most popular women's clothing items selling fast",
    "streetwear fashion trends Gen Z 2026",
    "sustainable fashion brands trending 2026",
    "luxury fashion bestsellers what's hot right now",
]

def fetch_exa_trends(queries: list = None, num_results: int = 5) -> list:
    """Fetch trend data from Exa semantic search."""
    if queries is None:
        queries = EXA_QUERIES
    
    all_results = []
    for query in queries:
        print(f"🔍 Exa: {query}")
        output = _run_mcporter(
            "exa.web_search_exa",
            query=query,
            numResults=num_results
        )
        if output:
            all_results.append({
                "query": query,
                "content": output,
                "source": "exa",
                "fetched_at": datetime.now().isoformat()
            })
    
    return all_results


def parse_exa_to_signals(exa_results: list) -> list:
    """Parse raw Exa results into structured trend signals."""
    import re
    signals = []
    
    # Price pattern: $XX.XX or $XXX
    price_re = re.compile(r'\$(\d+(?:\.\d{1,2})?)')
    # Common fashion categories
    cat_keywords = {
        "tops": ["top", "blouse", "shirt", "tee", "tank", "sweater", "hoodie", "cardigan"],
        "bottoms": ["pants", "jeans", "shorts", "skirt", "trousers", "leggings"],
        "dresses": ["dress", "gown", "romper", "jumpsuit"],
        "outerwear": ["jacket", "coat", "blazer", "puffer", "windbreaker"],
        "shoes": ["shoes", "sneakers", "boots", "heels", "sandals", "loafers"],
        "accessories": ["bag", "hat", "jewelry", "earrings", "necklace", "sunglasses", "watch", "belt"],
        "activewear": ["leggings", "sports bra", "activewear", "yoga", "athletic"],
    }
    # Known brands to detect
    known_brands = [
        "Nike", "Adidas", "Zara", "H&M", "Shein", "Gymshark", "Alo Yoga",
        "Lululemon", "Reformation", "Skims", "Free People", "Urban Outfitters",
        "Anthropologie", "Mango", "ASOS", "Uniqlo", "COS", "Arket",
        "Pangaia", "Vuori", "Kith", "Stussy", "Supreme", "Represent",
    ]
    
    for result in exa_results:
        content = result.get("content", "")
        if not content:
            continue
        
        # Split content into chunks (paragraphs or product-like blocks)
        lines = [l.strip() for l in content.split("\n") if l.strip() and len(l.strip()) > 10]
        
        for line in lines:
            lower = line.lower()
            
            # Try to extract price
            price_match = price_re.search(line)
            price = float(price_match.group(1)) if price_match else 0
            
            # Detect category
            category = ""
            for cat, kws in cat_keywords.items():
                if any(kw in lower for kw in kws):
                    category = cat
                    break
            
            # Detect brand
            brand = ""
            for b in known_brands:
                if b.lower() in lower:
                    brand = b
                    break
            
            # Only create signal if we found something useful
            if category or brand or price > 0:
                # Use first ~80 chars as title
                title = line[:80].strip()
                if len(line) > 80:
                    title = title.rsplit(" ", 1)[0] + "..."
                
                signals.append({
                    "source": "exa",
                    "signal_type": "article",
                    "title": title,
                    "url": "",
                    "content": line[:500],
                    "brand": brand,
                    "category": category,
                    "price": price,
                    "trend_score": 60,
                    "raw_data": {"query": result.get("query", ""), "fetched_at": result.get("fetched_at", "")},
                })
    
    print(f"📊 Parsed {len(signals)} signals from Exa results")
    return signals


# ============================================================
# Source 2: Scrapling — Shopify Store Scraping
# ============================================================

SHOPIFY_STORES = [
    # === Fast Fashion ===
    {"name": "Fashion Nova", "url": "https://www.fashionnova.com", "category": "fast-fashion"},
    {"name": "Princess Polly", "url": "https://www.princesspolly.com", "category": "fast-fashion"},
    {"name": "Oh Polly", "url": "https://www.ohpolly.com", "category": "fast-fashion"},
    {"name": "Hello Molly", "url": "https://www.hellomolly.com", "category": "fast-fashion"},
    {"name": "Cider", "url": "https://www.shopcider.com", "category": "fast-fashion"},
    {"name": "Edikted", "url": "https://www.edikted.com", "category": "fast-fashion"},

    # === Streetwear ===
    {"name": "Kith", "url": "https://kith.com", "category": "streetwear"},
    {"name": "BAPE", "url": "https://us.bape.com", "category": "streetwear"},
    {"name": "Essentials Fear of God", "url": "https://www.essentials-fog.com", "category": "streetwear"},
    {"name": "Represent", "url": "https://representclo.com", "category": "streetwear"},
    {"name": "Madhappy", "url": "https://www.madhappy.com", "category": "streetwear"},
    {"name": "Corteiz", "url": "https://www.corteiz.com", "category": "streetwear"},

    # === Women's Trendy ===
    {"name": "Meshki", "url": "https://www.meshki.us", "category": "trendy"},
    {"name": "Petal & Pup", "url": "https://www.petalandpup.com", "category": "trendy"},
    {"name": "Beginning Boutique", "url": "https://www.beginningboutique.com", "category": "trendy"},
    {"name": "Showpo", "url": "https://www.showpo.com", "category": "trendy"},
    {"name": "Dissh", "url": "https://www.dissh.com.au", "category": "trendy"},
    {"name": "Sabo Skirt", "url": "https://www.saboskirt.com", "category": "trendy"},
    {"name": "Verge Girl", "url": "https://www.vergegirl.com", "category": "trendy"},

    # === Sustainable Fashion ===
    {"name": "Girlfriend Collective", "url": "https://girlfriend.com", "category": "sustainable"},
    {"name": "Reformation", "url": "https://www.thereformation.com", "category": "sustainable"},
    {"name": "Pangaia", "url": "https://pangaia.com", "category": "sustainable"},
    {"name": "Tentree", "url": "https://www.tentree.com", "category": "sustainable"},
    {"name": "Organic Basics", "url": "https://www.organicbasics.com", "category": "sustainable"},

    # === Activewear ===
    {"name": "Gymshark", "url": "https://www.gymshark.com", "category": "activewear"},
    {"name": "Alo Yoga", "url": "https://www.aloyoga.com", "category": "activewear"},
    {"name": "Outdoor Voices", "url": "https://www.outdoorvoices.com", "category": "activewear"},
    {"name": "Vuori", "url": "https://vuori.com", "category": "activewear"},
    {"name": "Set Active", "url": "https://setactive.co", "category": "activewear"},
    {"name": "Halara", "url": "https://www.thehalara.com", "category": "activewear"},

    # === Kids (original TrendMuse focus) ===
    {"name": "Classic Whimsy", "url": "https://classicwhimsy.com", "category": "kids"},
    {"name": "Jamie Kay", "url": "https://www.jamiekay.com", "category": "kids"},
    {"name": "Stitchy Fish", "url": "https://stitchyfish.com", "category": "kids"},
]

def scrape_shopify_products(store: dict, max_products: int = 50) -> list:
    """Scrape products from a Shopify store using Scrapling."""
    url = store["url"]
    name = store["name"]
    print(f"🕷️ Scraping: {name} ({url})")
    
    # Try Shopify JSON API first (works for smaller stores)
    json_url = f"{url}/products.json?limit={max_products}"
    
    script = f'''
import sys
sys.path.insert(0, "{os.path.expanduser("~/.agent-reach-venv/lib/python3.13/site-packages")}")
from scrapling import Fetcher
import json

fetcher = Fetcher(auto_match=False)

# Try JSON API first
try:
    resp = fetcher.get("{json_url}", timeout=15)
    if resp.status == 200 and resp.body:
        data = json.loads(resp.body.decode("utf-8", errors="replace"))
        products = data.get("products", [])
        results = []
        for p in products[:{max_products}]:
            img = p.get("images", [{{}}])[0].get("src", "") if p.get("images") else ""
            price = p.get("variants", [{{}}])[0].get("price", "0") if p.get("variants") else "0"
            results.append({{
                "title": p.get("title", ""),
                "url": "{url}/products/" + p.get("handle", ""),
                "image": img,
                "price": float(price) if price else 0,
                "brand": "{name}",
                "category": p.get("product_type", "{store.get("category", "")}"),
                "tags": p.get("tags", []),
                "created_at": p.get("created_at", ""),
            }})
        print(json.dumps(results))
        sys.exit(0)
except Exception as e:
    pass

# Fallback: HTML scraping
try:
    resp = fetcher.get("{url}/collections/all", timeout=15)
    if resp.status == 200:
        # Extract product links from HTML
        links = resp.css('a[href*="/products/"]')
        products = []
        seen = set()
        for link in links[:{max_products}]:
            href = link.attrib.get("href", "")
            if href and href not in seen and "/products/" in href:
                seen.add(href)
                full_url = href if href.startswith("http") else "{url}" + href
                title_el = link.css("::text")
                title = title_el[0].strip() if title_el else href.split("/")[-1].replace("-", " ").title()
                img = ""
                img_el = link.css("img")
                if img_el:
                    img = img_el[0].attrib.get("src", "") or img_el[0].attrib.get("data-src", "")
                products.append({{
                    "title": title,
                    "url": full_url,
                    "image": img,
                    "brand": "{name}",
                    "category": "{store.get("category", "")}",
                }})
        print(json.dumps(products))
        sys.exit(0)
except Exception as e:
    print(json.dumps([]))
    sys.exit(1)

print(json.dumps([]))
'''
    
    venv_python = os.path.expanduser("~/.agent-reach-venv/bin/python3")
    try:
        result = subprocess.run(
            [venv_python, "-c", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            products = json.loads(result.stdout.strip())
            print(f"  ✅ Got {len(products)} products from {name}")
            return products
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"  ❌ Failed: {name} - {e}")
    
    return []


def scrape_all_stores(stores: list = None) -> list:
    """Scrape all configured Shopify stores."""
    if stores is None:
        stores = SHOPIFY_STORES
    
    all_products = []
    for store in stores:
        products = scrape_shopify_products(store)
        all_products.extend(products)
    
    print(f"\n📊 Total scraped: {len(all_products)} products from {len(stores)} stores")
    return all_products


# ============================================================
# Source 3: Twitter/X Fashion Trends via Agent Reach
# ============================================================

FASHION_TWITTER_QUERIES = [
    "fashion trend 2026",
    "viral outfit tiktok",
    "best selling fashion brand",
    "spring style trending",
]

def fetch_twitter_trends(queries: list = None) -> list:
    """Fetch fashion-related tweets via Agent Reach xreach."""
    if queries is None:
        queries = FASHION_TWITTER_QUERIES
    
    results = []
    for query in queries:
        print(f"🐦 X search: {query}")
        output = _run_agent_reach("xreach", "search", query=query, count="20")
        if output:
            results.append({
                "query": query,
                "content": output,
                "source": "twitter",
                "fetched_at": datetime.now().isoformat()
            })
    
    return results


# ============================================================
# Storage: Save to SQLite
# ============================================================

def store_signals(signals: list):
    """Store trend signals to database with dedup."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for signal in signals:
        content_hash = _content_hash(
            f"{signal.get('title', '')}{signal.get('url', '')}"
        )
        
        try:
            c.execute("""
                INSERT OR IGNORE INTO trend_signals 
                (source, signal_type, title, url, content, image_url, brand, 
                 category, price, trend_score, raw_data, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.get("source", "unknown"),
                signal.get("signal_type", "product"),
                signal.get("title", ""),
                signal.get("url", ""),
                signal.get("content", ""),
                signal.get("image", ""),
                signal.get("brand", ""),
                signal.get("category", ""),
                signal.get("price", 0),
                signal.get("trend_score", 50),
                json.dumps(signal.get("raw_data", {})),
                content_hash,
            ))
            if c.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except sqlite3.Error as e:
            print(f"  DB error: {e}")
            skipped += 1
    
    conn.commit()
    conn.close()
    print(f"💾 Stored: {inserted} new, {skipped} skipped (dupes)")
    return inserted


# ============================================================
# Main Pipeline
# ============================================================

def run_full_pipeline():
    """Run the complete trend data pipeline."""
    print("=" * 60)
    print(f"🚀 TrendMuse Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 0. Init tables
    init_trend_tables()
    
    # 1. Exa semantic search
    print("\n📡 Phase 1: Exa Semantic Search")
    exa_results = fetch_exa_trends(num_results=3)
    exa_signals = parse_exa_to_signals(exa_results)
    if exa_signals:
        store_signals(exa_signals)
    
    # 2. Shopify scraping
    print("\n🕷️ Phase 2: Shopify Store Scraping")
    products = scrape_all_stores()
    
    # Convert to signals and store
    signals = []
    for p in products:
        signals.append({
            "source": "scrapling",
            "signal_type": "product",
            "title": p.get("title", ""),
            "url": p.get("url", ""),
            "image": p.get("image", ""),
            "brand": p.get("brand", ""),
            "category": p.get("category", ""),
            "price": p.get("price", 0),
            "trend_score": 50,  # Base score, will be enhanced
            "raw_data": p,
        })
    
    store_signals(signals)
    
    # 3. Twitter trends
    print("\n🐦 Phase 3: Twitter Fashion Trends")
    twitter_results = fetch_twitter_trends()
    
    # 4. Summary
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM trend_signals").fetchone()[0]
    by_source = c.execute(
        "SELECT source, COUNT(*) FROM trend_signals GROUP BY source"
    ).fetchall()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Pipeline Complete!")
    print(f"   Total signals in DB: {total}")
    for source, count in by_source:
        print(f"   - {source}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    run_full_pipeline()
