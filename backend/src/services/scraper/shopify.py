"""
Shopify Generic Scraper

Works with any Shopify-based store by using the products.json API.
Supports: Classic Whimsy, Jamie Kay, Shrimp and Grits Kids, etc.
"""
import uuid
import aiohttp
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, urljoin

from .base import BaseScraper
from src.models.schemas import FashionItem, FashionCategory


class ShopifyScraper(BaseScraper):
    """
    Generic scraper for Shopify-based stores.
    
    Uses the Shopify Storefront JSON API:
    - /products.json - All products
    - /collections/{handle}/products.json - Products in a collection
    """
    
    # Site-specific configurations
    SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
        "classicwhimsy.com": {
            "name": "Classic Whimsy",
            "default_collection": "all",
            "categories": {
                "girls": FashionCategory.DRESS,
                "boys": FashionCategory.TOP,
                "baby": FashionCategory.ACCESSORIES,
                "dresses": FashionCategory.DRESS,
            }
        },
        "shrimpandgritskids.com": {
            "name": "Shrimp and Grits Kids",
            "default_collection": "all",
            "categories": {}
        },
        # Note: tullabee.com removed - uses TullabeeScraper (Cloudflare protected)
        "jamiekay.com": {
            "name": "Jamie Kay",
            "default_collection": "all",
            "categories": {}
        },
        "gigiandmax.com": {
            "name": "Gigi and Max",
            "default_collection": "all",
            "categories": {},
            "base_url": "https://www.gigiandmax.com"  # Requires www prefix
        },
        "stitchyfish.com": {
            "name": "Stitchy Fish",
            "default_collection": "all",
            "categories": {}
        },
        "littlebearsmocks.com": {
            "name": "Little Bear Smocks",
            "default_collection": "all",
            "categories": {}
        },
        "zuccinikids.com": {
            "name": "Zuccini Kids",
            "default_collection": "all",
            "categories": {}
        },
        "marienicoleclothing.com": {
            "name": "Marie Nicole Clothing",
            "default_collection": "all",
            "categories": {}
        },
        "morninglavender.com": {
            "name": "Morning Lavender",
            "default_collection": "all",
            "categories": {}
        },
        "matildajaneclothing.com": {
            "name": "Matilda Jane Clothing",
            "default_collection": "all",
            "categories": {}
        },
    }
    
    def __init__(self, timeout: int = 30000):
        super().__init__(timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    
    def _get_site_config(self, url: str) -> Dict[str, Any]:
        """Get site-specific configuration"""
        domain = self._get_domain(url)
        return self.SITE_CONFIGS.get(domain, {
            "name": domain,
            "default_collection": "all",
            "categories": {}
        })
    
    def _get_base_url(self, url: str) -> str:
        """Get base URL from input URL or site config"""
        # Check if there's a configured base_url for this domain
        site_config = self._get_site_config(url)
        if site_config.get("base_url"):
            return site_config["base_url"]
        
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _extract_collection(self, url: str) -> Optional[str]:
        """Extract collection handle from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        if "/collections/" in path:
            parts = path.split("/collections/")
            if len(parts) > 1:
                collection = parts[1].split("/")[0].split("?")[0]
                return collection
        return None
    
    def _map_category(self, product: Dict, site_config: Dict) -> FashionCategory:
        """Map Shopify product type to FashionCategory"""
        product_type = product.get("product_type", "").lower()
        tags = [t.lower() for t in product.get("tags", [])]
        
        # Check tags for gender/category hints
        if "dress" in product_type or any("dress" in t for t in tags):
            return FashionCategory.DRESS
        elif "top" in product_type or "shirt" in product_type:
            return FashionCategory.TOP
        elif "pant" in product_type or "short" in product_type:
            return FashionCategory.PANTS
        elif "jacket" in product_type or "coat" in product_type:
            return FashionCategory.JACKET
        elif "shoe" in product_type or "footwear" in product_type:
            return FashionCategory.SHOES
        elif "accessory" in product_type or "bow" in product_type:
            return FashionCategory.ACCESSORIES
        
        return FashionCategory.DRESS  # Default for kids clothing
    
    def _extract_colors(self, product: Dict) -> List[str]:
        """Extract colors from product tags or options"""
        colors = []
        tags = product.get("tags", [])
        
        for tag in tags:
            if tag.lower().startswith("color_"):
                colors.append(tag.split("_")[1].title())
        
        # Also check variant options
        for variant in product.get("variants", [])[:5]:
            option1 = variant.get("option1", "")
            if option1 and option1 not in colors:
                # Check if it looks like a color
                color_keywords = ["pink", "blue", "red", "white", "black", "green", "yellow", "purple", "gray", "navy"]
                if any(kw in option1.lower() for kw in color_keywords):
                    colors.append(option1)
        
        return colors[:5]  # Limit to 5 colors
    
    def _extract_tags(self, product: Dict) -> List[str]:
        """Extract relevant tags from product"""
        tags = product.get("tags", [])
        relevant_tags = []
        
        skip_prefixes = ["feed-", "supplier-", "return_", "season_"]
        
        for tag in tags:
            # Skip internal/system tags
            if any(tag.lower().startswith(p) for p in skip_prefixes):
                continue
            # Skip color tags (handled separately)
            if tag.lower().startswith("color_"):
                continue
            # Clean up tag
            clean_tag = tag.replace("_", " ").title()
            if len(clean_tag) > 2:
                relevant_tags.append(clean_tag)
        
        return relevant_tags[:10]  # Limit to 10 tags
    
    def _get_image_url(self, product: Dict) -> str:
        """Get the main product image URL"""
        images = product.get("images", [])
        if images:
            image = images[0]
            if isinstance(image, dict):
                return image.get("src", "")
            return str(image)
        return ""
    
    def _get_price(self, product: Dict) -> float:
        """Get product price from first available variant"""
        variants = product.get("variants", [])
        for variant in variants:
            price = variant.get("price")
            if price:
                try:
                    return float(price)
                except (ValueError, TypeError):
                    pass
        return 0.0
    
    def _get_inventory_status(self, product: Dict) -> dict:
        """Get inventory and popularity indicators"""
        variants = product.get("variants", [])
        total_inventory = 0
        available_count = 0
        
        for variant in variants:
            inventory = variant.get("inventory_quantity", 0)
            if inventory and inventory > 0:
                total_inventory += inventory
                available_count += 1
            elif variant.get("available", True):
                available_count += 1
        
        # Low stock = potentially popular
        is_low_stock = total_inventory > 0 and total_inventory < 10
        is_sold_out = available_count == 0
        
        return {
            "total_inventory": total_inventory,
            "variants_available": available_count,
            "total_variants": len(variants),
            "is_low_stock": is_low_stock,
            "is_sold_out": is_sold_out,
            "popularity_score": self._calculate_popularity(product, is_low_stock, is_sold_out)
        }
    
    def _calculate_popularity(self, product: Dict, is_low_stock: bool, is_sold_out: bool) -> int:
        """Calculate a popularity score (0-100) based on available signals"""
        score = 50  # Base score
        
        # Low stock suggests high demand
        if is_low_stock:
            score += 20
        
        # Position in collection (earlier = more featured)
        # This is handled externally based on position
        
        # Tags that suggest popularity
        tags = [t.lower() for t in product.get("tags", [])]
        popularity_tags = ["bestseller", "best-seller", "popular", "trending", "hot", "new-arrival", "featured"]
        for tag in popularity_tags:
            if any(tag in t for t in tags):
                score += 15
                break
        
        # Has been recently updated (product is being managed)
        updated_at = product.get("updated_at", "")
        if updated_at:
            # Recent updates suggest active product
            score += 5
        
        return min(100, score)
    
    def _get_original_price(self, product: Dict) -> Optional[float]:
        """Get original price (compare_at_price) if on sale"""
        variants = product.get("variants", [])
        for variant in variants:
            compare_price = variant.get("compare_at_price")
            if compare_price:
                try:
                    return float(compare_price)
                except (ValueError, TypeError):
                    pass
        return None
    
    async def scrape(
        self,
        url: str,
        max_items: int = 50,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """
        Scrape fashion items from a Shopify store
        
        Args:
            url: The store URL (can be base URL or collection URL)
            max_items: Maximum number of items to return
            category_filter: Optional category to filter by
            
        Returns:
            List of FashionItem objects
        """
        items = []
        base_url = self._get_base_url(url)
        site_config = self._get_site_config(url)
        
        # Determine collection
        collection = self._extract_collection(url)
        if not collection:
            collection = site_config.get("default_collection", "all")
        
        # Build API URL
        api_url = f"{base_url}/collections/{collection}/products.json"
        
        print(f"[ShopifyScraper] Fetching from: {api_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                page = 1
                while len(items) < max_items:
                    # Fetch products
                    params = {
                        "limit": min(250, max_items - len(items)),
                        "page": page
                    }
                    
                    async with session.get(
                        api_url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout / 1000)
                    ) as response:
                        if response.status != 200:
                            print(f"[ShopifyScraper] API error: {response.status}")
                            break
                        
                        data = await response.json()
                        products = data.get("products", [])
                        
                        if not products:
                            break  # No more products
                        
                        for product in products:
                            if len(items) >= max_items:
                                break
                            
                            # Map to FashionItem
                            category = self._map_category(product, site_config)
                            
                            # Apply category filter if specified
                            if category_filter and category != category_filter:
                                continue
                            
                            item = FashionItem(
                                id=str(product.get("id", uuid.uuid4())),
                                name=product.get("title", "Unknown"),
                                brand=product.get("vendor", site_config.get("name", "Unknown")),
                                price=self._get_price(product),
                                original_price=self._get_original_price(product),
                                currency="USD",
                                category=category,
                                colors=self._extract_colors(product),
                                tags=self._extract_tags(product),
                                image_url=self._get_image_url(product),
                                product_url=f"{base_url}/products/{product.get('handle', '')}",
                                rating=0.0,  # Shopify doesn't have ratings in API
                                reviews_count=0,
                                sales_count=0,
                                scraped_at=datetime.now()
                            )
                            
                            items.append(item)
                        
                        page += 1
                        
                        # Safety limit
                        if page > 20:
                            break
                            
        except Exception as e:
            print(f"[ShopifyScraper] Error: {e}")
        
        print(f"[ShopifyScraper] Found {len(items)} items from {site_config.get('name', 'Unknown')}")
        return items
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from description"""
        if not html:
            return ""
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()[:500]  # Limit length
    
    async def download_image(self, image_url: str, save_path: str) -> bool:
        """Download an image from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(save_path, "wb") as f:
                            f.write(content)
                        return True
        except Exception as e:
            print(f"[ShopifyScraper] Image download error: {e}")
        return False


# Convenience function to check if a URL is a Shopify store
def is_shopify_store(url: str) -> bool:
    """Check if URL is a known Shopify store"""
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in ShopifyScraper.SITE_CONFIGS
