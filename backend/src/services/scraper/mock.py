"""
Mock scraper with sample fashion data for demo purposes
"""
import random
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import aiohttp
from pathlib import Path

from .base import BaseScraper
from src.models.schemas import FashionItem, FashionCategory, TrendLevel


# Sample fashion data for demo
MOCK_FASHION_DATA = [
    # Dresses
    {"name": "Floral Maxi Dress", "category": FashionCategory.DRESS, "price": 89.99, "colors": ["Coral", "Navy"], "tags": ["summer", "boho", "floral"]},
    {"name": "Satin Slip Dress", "category": FashionCategory.DRESS, "price": 129.99, "colors": ["Champagne", "Black"], "tags": ["elegant", "evening", "minimalist"]},
    {"name": "Knit Midi Dress", "category": FashionCategory.DRESS, "price": 79.99, "colors": ["Camel", "Olive"], "tags": ["casual", "fall", "cozy"]},
    {"name": "Sequin Mini Dress", "category": FashionCategory.DRESS, "price": 149.99, "colors": ["Silver", "Gold"], "tags": ["party", "sparkle", "nye"]},
    {"name": "Linen Wrap Dress", "category": FashionCategory.DRESS, "price": 99.99, "colors": ["White", "Sage"], "tags": ["summer", "natural", "classic"]},
    
    # Tops
    {"name": "Oversized Blazer Top", "category": FashionCategory.TOP, "price": 119.99, "colors": ["Black", "Beige"], "tags": ["power", "professional", "trending"]},
    {"name": "Cropped Cardigan", "category": FashionCategory.TOP, "price": 59.99, "colors": ["Pink", "Lavender", "Cream"], "tags": ["y2k", "cute", "layering"]},
    {"name": "Silk Button-Up", "category": FashionCategory.TOP, "price": 139.99, "colors": ["Ivory", "Navy"], "tags": ["luxe", "classic", "versatile"]},
    {"name": "Graphic Print Tee", "category": FashionCategory.TOP, "price": 34.99, "colors": ["White", "Black"], "tags": ["streetwear", "casual", "vintage"]},
    {"name": "Ruched Mesh Top", "category": FashionCategory.TOP, "price": 44.99, "colors": ["Black", "Red", "Nude"], "tags": ["going-out", "sexy", "trendy"]},
    {"name": "Cable Knit Sweater", "category": FashionCategory.TOP, "price": 89.99, "colors": ["Cream", "Forest"], "tags": ["cozy", "fall", "classic"]},
    
    # Pants
    {"name": "Wide Leg Trousers", "category": FashionCategory.PANTS, "price": 79.99, "colors": ["Black", "Tan", "Grey"], "tags": ["office", "chic", "comfortable"]},
    {"name": "Leather Straight Leg", "category": FashionCategory.PANTS, "price": 159.99, "colors": ["Black", "Brown"], "tags": ["edgy", "luxe", "trending"]},
    {"name": "High-Rise Mom Jeans", "category": FashionCategory.PANTS, "price": 69.99, "colors": ["Light Wash", "Dark Wash"], "tags": ["denim", "vintage", "everyday"]},
    {"name": "Pleated Palazzo Pants", "category": FashionCategory.PANTS, "price": 89.99, "colors": ["Olive", "Cream"], "tags": ["flowy", "elegant", "summer"]},
    
    # Skirts
    {"name": "Pleated Midi Skirt", "category": FashionCategory.SKIRT, "price": 69.99, "colors": ["Navy", "Burgundy"], "tags": ["classic", "feminine", "office"]},
    {"name": "Denim Mini Skirt", "category": FashionCategory.SKIRT, "price": 49.99, "colors": ["Blue", "White"], "tags": ["casual", "y2k", "summer"]},
    {"name": "Satin Maxi Skirt", "category": FashionCategory.SKIRT, "price": 99.99, "colors": ["Champagne", "Forest"], "tags": ["elegant", "evening", "flowing"]},
    
    # Jackets
    {"name": "Cropped Leather Jacket", "category": FashionCategory.JACKET, "price": 249.99, "colors": ["Black", "Brown"], "tags": ["edgy", "classic", "investment"]},
    {"name": "Oversized Denim Jacket", "category": FashionCategory.JACKET, "price": 89.99, "colors": ["Light Wash", "Black"], "tags": ["casual", "layering", "vintage"]},
    {"name": "Quilted Bomber", "category": FashionCategory.JACKET, "price": 129.99, "colors": ["Olive", "Black", "Cream"], "tags": ["sporty", "warm", "trendy"]},
    
    # Coats
    {"name": "Wool Blend Overcoat", "category": FashionCategory.COAT, "price": 299.99, "colors": ["Camel", "Black", "Grey"], "tags": ["classic", "winter", "investment"]},
    {"name": "Faux Fur Teddy Coat", "category": FashionCategory.COAT, "price": 179.99, "colors": ["Cream", "Brown"], "tags": ["cozy", "statement", "winter"]},
    
    # Activewear
    {"name": "High-Waist Leggings", "category": FashionCategory.ACTIVEWEAR, "price": 79.99, "colors": ["Black", "Navy", "Burgundy"], "tags": ["workout", "athleisure", "sculpting"]},
    {"name": "Sports Bra Set", "category": FashionCategory.ACTIVEWEAR, "price": 59.99, "colors": ["Black", "White", "Rose"], "tags": ["gym", "matching", "support"]},
    
    # Accessories
    {"name": "Structured Tote Bag", "category": FashionCategory.ACCESSORIES, "price": 189.99, "colors": ["Black", "Tan", "Cream"], "tags": ["work", "everyday", "classic"]},
    {"name": "Chain Link Belt", "category": FashionCategory.ACCESSORIES, "price": 49.99, "colors": ["Gold", "Silver"], "tags": ["statement", "90s", "versatile"]},
]

# Sample image URLs (using placeholder images)
PLACEHOLDER_IMAGES = [
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400",  # Fashion
    "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",  # Dress
    "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400",  # Outfit
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400",  # Clothes
    "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400",  # Fashion store
    "https://images.unsplash.com/photo-1558171813-4c088753af8f?w=400",  # Jacket
    "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=400",  # Pants
    "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=400",  # Shirt
]


class MockScraper(BaseScraper):
    """
    Mock scraper that returns sample fashion data for demo purposes
    """
    
    async def scrape(
        self, 
        url: str, 
        max_items: int = 20,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """Generate mock fashion items"""
        items = []
        
        # Filter by category if specified
        available_items = MOCK_FASHION_DATA
        if category_filter:
            available_items = [item for item in MOCK_FASHION_DATA if item["category"] == category_filter]
        
        # Create fashion items
        for i, data in enumerate(available_items[:max_items]):
            # Generate random metrics for demo
            reviews = random.randint(50, 2000)
            rating = round(random.uniform(3.5, 5.0), 1)
            sales = random.randint(100, 10000)
            
            item = FashionItem(
                id=str(uuid.uuid4()),
                name=data["name"],
                price=data["price"],
                currency="USD",
                original_price=data["price"] * random.uniform(1.1, 1.5) if random.random() > 0.5 else None,
                image_url=random.choice(PLACEHOLDER_IMAGES),
                product_url=f"{url}/product/{i+1}",
                category=data["category"],
                brand=self._extract_brand_from_url(url),
                reviews_count=reviews,
                rating=rating,
                sales_count=sales,
                colors=data["colors"],
                tags=data["tags"],
                scraped_at=datetime.now() - timedelta(minutes=random.randint(0, 60))
            )
            
            # Calculate trend score
            item.trend_score = self.calculate_trend_score(item)
            item.trend_level = self._get_trend_level(item.trend_score)
            
            items.append(item)
        
        # Sort by trend score
        items.sort(key=lambda x: x.trend_score, reverse=True)
        
        return items
    
    def _extract_brand_from_url(self, url: str) -> str:
        """Extract brand name from URL"""
        from urllib.parse import urlparse
        
        # Check for known brands in URL
        known_brands = {
            "shein": "SHEIN",
            "zara": "Zara",
            "hm": "H&M",
            "asos": "ASOS",
            "forever21": "Forever 21",
            "uniqlo": "UNIQLO",
            "mango": "Mango",
            "nordstrom": "Nordstrom",
            "revolve": "Revolve",
        }
        
        url_lower = url.lower()
        for key, brand in known_brands.items():
            if key in url_lower:
                return brand
        
        # Default: extract from domain
        try:
            domain = urlparse(url).netloc
            brand = domain.replace("www.", "").split(".")[0]
            return brand.title()
        except:
            return "TrendMuse"
    
    def _get_trend_level(self, score: float) -> TrendLevel:
        """Get trend level based on score"""
        if score >= 75:
            return TrendLevel.HOT
        elif score >= 50:
            return TrendLevel.RISING
        elif score >= 25:
            return TrendLevel.STABLE
        else:
            return TrendLevel.DECLINING
    
    async def download_image(self, image_url: str, save_path: str) -> bool:
        """Download image from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(content)
                        return True
        except Exception as e:
            print(f"Error downloading image: {e}")
        return False
