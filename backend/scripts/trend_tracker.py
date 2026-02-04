#!/usr/bin/env python3
"""
TrendMuse Trend Tracker

追踪 Shopify 独立品牌的热销趋势：
1. Best Sellers 集合排名变化
2. 库存变化 (sold out → 热销信号)
3. 周/月对比，找出 trending up 的款式
"""
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.scraper import ShopifyScraper
from src.services.database import DatabaseService


# 10个 Shopify 独立品牌的 Best Sellers 集合
BESTSELLER_COLLECTIONS = {
    "classicwhimsy.com": "https://classicwhimsy.com/collections/best-sellers",
    "jamiekay.com": "https://jamiekay.com/collections/best-sellers",
    "shrimpandgritskids.com": "https://shrimpandgritskids.com/collections/best-sellers",
    "gigiandmax.com": "https://www.gigiandmax.com/collections/best-sellers",
    "stitchyfish.com": "https://stitchyfish.com/collections/best-sellers",
    "littlebearsmocks.com": "https://littlebearsmocks.com/collections/best-sellers",
    "zuccinikids.com": "https://zuccinikids.com/collections/best-sellers",
    "marienicoleclothing.com": "https://marienicoleclothing.com/collections/best-sellers",
    "morninglavender.com": "https://morninglavender.com/collections/best-sellers",
    "matildajaneclothing.com": "https://matildajaneclothing.com/collections/best-sellers",
}


class TrendTracker:
    """追踪热销趋势"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "trendmuse.db"
        self.db = DatabaseService(str(db_path))
        self.scraper = ShopifyScraper()
        self._init_tracking_tables()
    
    def _init_tracking_tables(self):
        """创建趋势追踪表"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 排名历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bestseller_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    source TEXT,
                    rank INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # 库存变化表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    previous_status TEXT,
                    new_status TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # 趋势汇总表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER UNIQUE,
                    trend_score REAL DEFAULT 0,
                    rank_trend TEXT,  -- 'up', 'down', 'stable', 'new'
                    weeks_in_bestseller INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            conn.commit()
    
    async def track_bestsellers(self) -> Dict:
        """追踪所有品牌的 Best Sellers"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "brands": {},
            "trending_up": [],
            "new_entries": [],
            "sold_out": []
        }
        
        for source, url in BESTSELLER_COLLECTIONS.items():
            print(f"\n📊 Tracking: {source}")
            try:
                # 爬取当前 Best Sellers
                items = await self.scraper.scrape(url, max_items=50)
                
                if not items:
                    print(f"  ⚠️ No items found")
                    continue
                
                brand_result = {
                    "count": len(items),
                    "top_5": [],
                    "rank_changes": []
                }
                
                for rank, item in enumerate(items, 1):
                    # 保存到数据库
                    product_id, is_new = self.db.upsert_product(item, source=source)
                    
                    # 记录排名
                    self._record_ranking(product_id, source, rank)
                    
                    # 检查排名变化
                    rank_change = self._get_rank_change(product_id, source)
                    
                    if rank <= 5:
                        brand_result["top_5"].append({
                            "rank": rank,
                            "name": item.name[:40],
                            "price": item.price,
                            "change": rank_change
                        })
                    
                    # 标记趋势
                    if is_new:
                        results["new_entries"].append({
                            "source": source,
                            "name": item.name,
                            "rank": rank
                        })
                    elif rank_change and rank_change < 0:  # 排名上升 (数字变小)
                        results["trending_up"].append({
                            "source": source,
                            "name": item.name,
                            "rank": rank,
                            "change": rank_change
                        })
                    
                    # 更新趋势分数
                    self._update_trend_score(product_id, rank, rank_change, is_new)
                
                results["brands"][source] = brand_result
                print(f"  ✅ Tracked {len(items)} items")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results["brands"][source] = {"error": str(e)}
        
        return results
    
    def _record_ranking(self, product_id: int, source: str, rank: int):
        """记录排名"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bestseller_rankings (product_id, source, rank)
                VALUES (?, ?, ?)
            """, (product_id, source, rank))
    
    def _get_rank_change(self, product_id: int, source: str) -> Optional[int]:
        """获取排名变化 (负数=上升, 正数=下降)"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rank FROM bestseller_rankings
                WHERE product_id = ? AND source = ?
                ORDER BY recorded_at DESC
                LIMIT 2
            """, (product_id, source))
            
            rows = cursor.fetchall()
            if len(rows) >= 2:
                current_rank = rows[0]['rank']
                previous_rank = rows[1]['rank']
                return current_rank - previous_rank  # 负数=排名上升
        
        return None
    
    def _update_trend_score(self, product_id: int, rank: int, rank_change: Optional[int], is_new: bool):
        """更新趋势分数"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # 计算趋势分数
            # 排名越高分数越高，排名上升加分
            base_score = max(0, 50 - rank)  # 排名1=49分, 排名50=0分
            
            if rank_change:
                trend_bonus = -rank_change * 2  # 每上升1名加2分
            else:
                trend_bonus = 0
            
            trend_score = base_score + trend_bonus
            
            # 确定趋势方向
            if is_new:
                rank_trend = "new"
            elif rank_change and rank_change < -3:
                rank_trend = "up"
            elif rank_change and rank_change > 3:
                rank_trend = "down"
            else:
                rank_trend = "stable"
            
            cursor.execute("""
                INSERT INTO trend_scores (product_id, trend_score, rank_trend, weeks_in_bestseller)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(product_id) DO UPDATE SET
                    trend_score = ?,
                    rank_trend = ?,
                    weeks_in_bestseller = weeks_in_bestseller + 1,
                    last_updated = CURRENT_TIMESTAMP
            """, (product_id, trend_score, rank_trend, trend_score, rank_trend))
    
    def get_top_trending(self, limit: int = 20) -> List[Dict]:
        """获取趋势最强的产品"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.name, p.price, p.source, p.image_url, p.product_url,
                    t.trend_score, t.rank_trend, t.weeks_in_bestseller
                FROM trend_scores t
                JOIN products p ON t.product_id = p.id
                WHERE t.rank_trend IN ('up', 'new')
                ORDER BY t.trend_score DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_consistent_bestsellers(self, min_weeks: int = 3) -> List[Dict]:
        """获取持续热销的产品"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.name, p.price, p.source, p.image_url,
                    t.weeks_in_bestseller, t.trend_score
                FROM trend_scores t
                JOIN products p ON t.product_id = p.id
                WHERE t.weeks_in_bestseller >= ?
                ORDER BY t.weeks_in_bestseller DESC, t.trend_score DESC
                LIMIT 20
            """, (min_weeks,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def generate_report(self, tracking_results: Dict) -> str:
        """生成趋势报告"""
        report = f"""
🎨 TrendMuse 热销趋势报告
📅 {tracking_results['timestamp'][:10]}

━━━━━━━━━━━━━━━━━━━━━━
📈 本周趋势上升 (Trending Up)
━━━━━━━━━━━━━━━━━━━━━━
"""
        for item in tracking_results.get("trending_up", [])[:10]:
            report += f"• [{item['source'][:15]}] {item['name'][:30]} (↑{-item['change']}名)\n"
        
        report += """
━━━━━━━━━━━━━━━━━━━━━━
🆕 新进榜单 (New Entries)
━━━━━━━━━━━━━━━━━━━━━━
"""
        for item in tracking_results.get("new_entries", [])[:10]:
            report += f"• [{item['source'][:15]}] {item['name'][:30]} (第{item['rank']}名)\n"
        
        report += """
━━━━━━━━━━━━━━━━━━━━━━
🏆 各品牌 Top 3
━━━━━━━━━━━━━━━━━━━━━━
"""
        for source, data in tracking_results.get("brands", {}).items():
            if "error" in data:
                continue
            report += f"\n{source}:\n"
            for item in data.get("top_5", [])[:3]:
                change_str = ""
                if item.get("change"):
                    if item["change"] < 0:
                        change_str = f" ↑{-item['change']}"
                    elif item["change"] > 0:
                        change_str = f" ↓{item['change']}"
                report += f"  {item['rank']}. {item['name'][:25]} ${item['price']}{change_str}\n"
        
        return report


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TrendMuse Trend Tracker")
    parser.add_argument("--report", action="store_true", help="Generate trend report")
    parser.add_argument("--top", type=int, default=20, help="Show top N trending items")
    args = parser.parse_args()
    
    tracker = TrendTracker()
    
    print("🔍 Starting trend tracking...")
    results = await tracker.track_bestsellers()
    
    # 生成报告
    report = tracker.generate_report(results)
    print(report)
    
    # 保存结果
    output_path = Path(__file__).parent.parent / "data" / "trend_report_latest.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {output_path}")
    
    # 显示趋势最强的产品
    print("\n🔥 Top Trending Products:")
    for item in tracker.get_top_trending(10):
        print(f"  • {item['name'][:35]} ({item['source']}) - Score: {item['trend_score']}")


if __name__ == "__main__":
    asyncio.run(main())
