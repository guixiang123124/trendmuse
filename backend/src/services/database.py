"""
SQLite Database Service for TrendMuse

Stores scraped products, price history, and trend data.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from src.models.schemas import FashionItem, FashionCategory


class DatabaseService:
    """
    SQLite database service for storing and querying fashion data.
    
    Tables:
    - products: Main product information
    - scrape_sessions: Record of each scrape run
    - price_history: Track price changes over time
    - trends: Aggregated trend data by category/brand
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "trendmuse.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    external_id TEXT,
                    name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    source TEXT NOT NULL,
                    product_url TEXT,
                    image_url TEXT,
                    category TEXT,
                    price REAL,
                    original_price REAL,
                    currency TEXT DEFAULT 'USD',
                    colors TEXT,
                    tags TEXT,
                    rating REAL DEFAULT 0,
                    reviews_count INTEGER DEFAULT 0,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    UNIQUE(external_id, source)
                )
            """)
            
            # Scrape sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    url TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    items_found INTEGER DEFAULT 0,
                    items_new INTEGER DEFAULT 0,
                    items_updated INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',
                    error TEXT
                )
            """)
            
            # Price history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    original_price REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # Trends table (aggregated data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period TEXT NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    source TEXT,
                    category TEXT,
                    brand TEXT,
                    total_products INTEGER DEFAULT 0,
                    new_products INTEGER DEFAULT 0,
                    avg_price REAL,
                    min_price REAL,
                    max_price REAL,
                    top_colors TEXT,
                    top_tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(period, period_start, source, category, brand)
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_source ON products(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_last_seen ON products(last_seen_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_period ON trends(period, period_start)")
    
    # ==================== Product Operations ====================
    
    def upsert_product(self, item: FashionItem, source: str) -> tuple[str, bool]:
        """
        Insert or update a product.
        
        Returns:
            Tuple of (product_id, is_new)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if product exists
            cursor.execute(
                "SELECT id, price FROM products WHERE external_id = ? AND source = ?",
                (item.id, source)
            )
            existing = cursor.fetchone()
            
            colors_json = json.dumps(item.colors)
            tags_json = json.dumps(item.tags)
            
            if existing:
                # Update existing product
                product_id = existing['id']
                old_price = existing['price']
                
                cursor.execute("""
                    UPDATE products SET
                        name = ?,
                        price = ?,
                        original_price = ?,
                        image_url = ?,
                        product_url = ?,
                        category = ?,
                        colors = ?,
                        tags = ?,
                        rating = ?,
                        reviews_count = ?,
                        last_seen_at = ?,
                        is_active = 1
                    WHERE id = ?
                """, (
                    item.name, item.price, item.original_price,
                    item.image_url, item.product_url, item.category.value,
                    colors_json, tags_json, item.rating, item.reviews_count,
                    datetime.now(), product_id
                ))
                
                # Record price change if different
                if old_price != item.price:
                    self._record_price_change(cursor, product_id, item.price, item.original_price)
                
                return product_id, False
            else:
                # Insert new product
                import uuid
                product_id = str(uuid.uuid4())
                
                cursor.execute("""
                    INSERT INTO products (
                        id, external_id, name, brand, source, product_url, image_url,
                        category, price, original_price, currency, colors, tags,
                        rating, reviews_count, first_seen_at, last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, item.id, item.name, item.brand, source,
                    item.product_url, item.image_url, item.category.value,
                    item.price, item.original_price, item.currency,
                    colors_json, tags_json, item.rating, item.reviews_count,
                    datetime.now(), datetime.now()
                ))
                
                # Record initial price
                self._record_price_change(cursor, product_id, item.price, item.original_price)
                
                return product_id, True
    
    def _record_price_change(self, cursor, product_id: str, price: float, original_price: float = None):
        """Record a price change in history"""
        cursor.execute("""
            INSERT INTO price_history (product_id, price, original_price)
            VALUES (?, ?, ?)
        """, (product_id, price, original_price))
    
    def bulk_upsert_products(self, items: List[FashionItem], source: str) -> Dict[str, int]:
        """
        Bulk insert/update products.
        
        Returns:
            Dict with counts: {'total': N, 'new': N, 'updated': N}
        """
        stats = {'total': 0, 'new': 0, 'updated': 0}
        
        for item in items:
            product_id, is_new = self.upsert_product(item, source)
            stats['total'] += 1
            if is_new:
                stats['new'] += 1
            else:
                stats['updated'] += 1
        
        return stats
    
    def get_products(
        self,
        source: str = None,
        category: str = None,
        brand: str = None,
        min_price: float = None,
        max_price: float = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Query products with filters"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if source:
                query += " AND source = ?"
                params.append(source)
            if category:
                query += " AND category = ?"
                params.append(category)
            if brand:
                query += " AND brand = ?"
                params.append(brand)
            if min_price is not None:
                query += " AND price >= ?"
                params.append(min_price)
            if max_price is not None:
                query += " AND price <= ?"
                params.append(max_price)
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY last_seen_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
    
    def get_product_count(self, source: str = None, active_only: bool = True) -> int:
        """Get total product count"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) as count FROM products WHERE 1=1"
            params = []
            
            if source:
                query += " AND source = ?"
                params.append(source)
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            return cursor.fetchone()['count']
    
    def get_product_by_url(self, product_url: str) -> Optional[Dict]:
        """Get a product by its URL"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM products WHERE product_url = ?",
                (product_url,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def get_product_by_external_id(self, external_id: str, source: str) -> Optional[Dict]:
        """Get a product by external ID and source"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM products WHERE external_id = ? AND source = ?",
                (external_id, source)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    # ==================== Scrape Session Operations ====================
    
    def start_scrape_session(self, source: str, url: str = None) -> int:
        """Start a new scrape session and return its ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scrape_sessions (source, url) VALUES (?, ?)",
                (source, url)
            )
            return cursor.lastrowid
    
    def complete_scrape_session(
        self,
        session_id: int,
        items_found: int,
        items_new: int,
        items_updated: int,
        error: str = None
    ):
        """Mark a scrape session as complete"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            status = 'failed' if error else 'completed'
            cursor.execute("""
                UPDATE scrape_sessions SET
                    completed_at = ?,
                    items_found = ?,
                    items_new = ?,
                    items_updated = ?,
                    status = ?,
                    error = ?
                WHERE id = ?
            """, (datetime.now(), items_found, items_new, items_updated, status, error, session_id))
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent scrape sessions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scrape_sessions
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Trend Operations ====================
    
    def calculate_trends(self, period: str = 'weekly') -> Dict[str, Any]:
        """
        Calculate and store trend data.
        
        Args:
            period: 'daily', 'weekly', or 'monthly'
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Determine date range
            today = datetime.now().date()
            if period == 'daily':
                start_date = today
                end_date = today
            elif period == 'weekly':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # monthly
                start_date = today.replace(day=1)
                next_month = today.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
            
            # Calculate trends by source
            cursor.execute("""
                SELECT 
                    source,
                    category,
                    brand,
                    COUNT(*) as total_products,
                    SUM(CASE WHEN date(first_seen_at) >= ? THEN 1 ELSE 0 END) as new_products,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price
                FROM products
                WHERE is_active = 1 AND date(last_seen_at) >= ?
                GROUP BY source, category, brand
            """, (start_date, start_date))
            
            trends = []
            for row in cursor.fetchall():
                # Get top colors and tags
                colors, tags = self._get_top_attributes(
                    cursor, row['source'], row['category'], row['brand']
                )
                
                trend_data = {
                    'period': period,
                    'period_start': start_date,
                    'period_end': end_date,
                    'source': row['source'],
                    'category': row['category'],
                    'brand': row['brand'],
                    'total_products': row['total_products'],
                    'new_products': row['new_products'],
                    'avg_price': round(row['avg_price'], 2) if row['avg_price'] else 0,
                    'min_price': row['min_price'],
                    'max_price': row['max_price'],
                    'top_colors': json.dumps(colors),
                    'top_tags': json.dumps(tags)
                }
                trends.append(trend_data)
                
                # Upsert trend record
                cursor.execute("""
                    INSERT OR REPLACE INTO trends (
                        period, period_start, period_end, source, category, brand,
                        total_products, new_products, avg_price, min_price, max_price,
                        top_colors, top_tags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    period, start_date, end_date, row['source'], row['category'], row['brand'],
                    row['total_products'], row['new_products'], trend_data['avg_price'],
                    row['min_price'], row['max_price'], trend_data['top_colors'],
                    trend_data['top_tags'], datetime.now()
                ))
            
            return {
                'period': period,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'trends_count': len(trends)
            }
    
    def _get_top_attributes(self, cursor, source: str, category: str, brand: str) -> tuple:
        """Get top colors and tags for a group"""
        cursor.execute("""
            SELECT colors, tags FROM products
            WHERE source = ? AND category = ? AND brand = ? AND is_active = 1
        """, (source, category, brand))
        
        color_counts = {}
        tag_counts = {}
        
        for row in cursor.fetchall():
            colors = json.loads(row['colors'] or '[]')
            tags = json.loads(row['tags'] or '[]')
            
            for c in colors:
                color_counts[c] = color_counts.get(c, 0) + 1
            for t in tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        
        top_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [c[0] for c in top_colors], [t[0] for t in top_tags]
    
    def get_trends(
        self,
        period: str = 'weekly',
        source: str = None,
        category: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Query stored trends"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM trends WHERE period = ?"
            params = [period]
            
            if source:
                query += " AND source = ?"
                params.append(source)
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY period_start DESC, total_products DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total products
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE is_active = 1")
            total_products = cursor.fetchone()['count']
            
            # Products by source
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM products WHERE is_active = 1 
                GROUP BY source ORDER BY count DESC
            """)
            by_source = {row['source']: row['count'] for row in cursor.fetchall()}
            
            # Products by category
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM products WHERE is_active = 1 
                GROUP BY category ORDER BY count DESC
            """)
            by_category = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) as count FROM products
                WHERE date(last_seen_at) = date('now')
            """)
            updated_today = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM products
                WHERE date(first_seen_at) = date('now')
            """)
            new_today = cursor.fetchone()['count']
            
            return {
                'total_products': total_products,
                'by_source': by_source,
                'by_category': by_category,
                'updated_today': updated_today,
                'new_today': new_today,
                'db_path': str(self.db_path)
            }
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert sqlite Row to dict"""
        if row is None:
            return None
        d = dict(row)
        # Parse JSON fields
        for key in ['colors', 'tags', 'top_colors', 'top_tags']:
            if key in d and d[key]:
                try:
                    d[key] = json.loads(d[key])
                except:
                    pass
        return d


# Singleton instance
_db_instance: Optional[DatabaseService] = None

def get_database() -> DatabaseService:
    """Get or create database service singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseService()
    return _db_instance
