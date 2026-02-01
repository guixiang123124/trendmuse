"""
Trend Analysis Service

Analyzes scraped fashion items to identify trends and patterns.
"""
from typing import List, Dict, Any
from collections import Counter
from src.models.schemas import FashionItem, FashionCategory, TrendLevel


class TrendAnalyzer:
    """
    Analyzes fashion items to identify trends
    """
    
    def analyze_items(self, items: List[FashionItem]) -> Dict[str, Any]:
        """
        Comprehensive trend analysis of fashion items
        
        Returns:
            Dictionary with various trend insights
        """
        if not items:
            return {"error": "No items to analyze"}
        
        return {
            "summary": self._get_summary(items),
            "top_categories": self._analyze_categories(items),
            "trending_colors": self._analyze_colors(items),
            "popular_tags": self._analyze_tags(items),
            "price_analysis": self._analyze_prices(items),
            "trend_distribution": self._analyze_trend_levels(items),
            "hot_items": self._get_hot_items(items),
        }
    
    def _get_summary(self, items: List[FashionItem]) -> Dict[str, Any]:
        """Get summary statistics"""
        prices = [item.price for item in items]
        trend_scores = [item.trend_score for item in items]
        
        return {
            "total_items": len(items),
            "avg_price": round(sum(prices) / len(prices), 2),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_trend_score": round(sum(trend_scores) / len(trend_scores), 1),
            "total_reviews": sum(item.reviews_count for item in items),
            "total_sales": sum(item.sales_count for item in items),
        }
    
    def _analyze_categories(self, items: List[FashionItem]) -> List[Dict[str, Any]]:
        """Analyze category distribution"""
        category_counter = Counter(item.category.value for item in items)
        category_scores = {}
        
        for item in items:
            cat = item.category.value
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(item.trend_score)
        
        results = []
        for category, count in category_counter.most_common():
            avg_score = sum(category_scores[category]) / len(category_scores[category])
            results.append({
                "category": category,
                "count": count,
                "percentage": round(count / len(items) * 100, 1),
                "avg_trend_score": round(avg_score, 1),
            })
        
        return results
    
    def _analyze_colors(self, items: List[FashionItem]) -> List[Dict[str, Any]]:
        """Analyze color trends"""
        all_colors = []
        color_scores = {}
        
        for item in items:
            for color in item.colors:
                all_colors.append(color.lower())
                if color.lower() not in color_scores:
                    color_scores[color.lower()] = []
                color_scores[color.lower()].append(item.trend_score)
        
        color_counter = Counter(all_colors)
        
        results = []
        for color, count in color_counter.most_common(10):
            avg_score = sum(color_scores[color]) / len(color_scores[color])
            results.append({
                "color": color.title(),
                "count": count,
                "avg_trend_score": round(avg_score, 1),
            })
        
        return results
    
    def _analyze_tags(self, items: List[FashionItem]) -> List[Dict[str, Any]]:
        """Analyze popular tags/keywords"""
        all_tags = []
        tag_scores = {}
        
        for item in items:
            for tag in item.tags:
                all_tags.append(tag.lower())
                if tag.lower() not in tag_scores:
                    tag_scores[tag.lower()] = []
                tag_scores[tag.lower()].append(item.trend_score)
        
        tag_counter = Counter(all_tags)
        
        results = []
        for tag, count in tag_counter.most_common(15):
            avg_score = sum(tag_scores[tag]) / len(tag_scores[tag])
            results.append({
                "tag": tag,
                "count": count,
                "avg_trend_score": round(avg_score, 1),
            })
        
        return results
    
    def _analyze_prices(self, items: List[FashionItem]) -> Dict[str, Any]:
        """Analyze price distribution"""
        prices = [item.price for item in items]
        
        # Price ranges
        ranges = {
            "budget": (0, 50),
            "mid_range": (50, 100),
            "premium": (100, 200),
            "luxury": (200, float('inf')),
        }
        
        distribution = {}
        for range_name, (low, high) in ranges.items():
            items_in_range = [item for item in items if low <= item.price < high]
            if items_in_range:
                distribution[range_name] = {
                    "count": len(items_in_range),
                    "percentage": round(len(items_in_range) / len(items) * 100, 1),
                    "avg_trend_score": round(sum(i.trend_score for i in items_in_range) / len(items_in_range), 1),
                }
        
        return {
            "distribution": distribution,
            "median_price": sorted(prices)[len(prices) // 2],
            "price_range": {"min": min(prices), "max": max(prices)},
        }
    
    def _analyze_trend_levels(self, items: List[FashionItem]) -> Dict[str, int]:
        """Analyze distribution of trend levels"""
        level_counter = Counter(item.trend_level.value for item in items)
        return dict(level_counter)
    
    def _get_hot_items(self, items: List[FashionItem], limit: int = 5) -> List[Dict[str, Any]]:
        """Get the hottest trending items"""
        hot_items = sorted(items, key=lambda x: x.trend_score, reverse=True)[:limit]
        
        return [
            {
                "id": item.id,
                "name": item.name,
                "trend_score": item.trend_score,
                "price": item.price,
                "category": item.category.value,
            }
            for item in hot_items
        ]
