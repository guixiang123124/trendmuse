"""
Generic e-commerce scraper using Playwright
"""
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from .base import BaseScraper
from src.models.schemas import FashionItem, FashionCategory, TrendLevel
from src.core.config import get_settings

# Playwright import with fallback
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class GenericScraper(BaseScraper):
    """
    Generic scraper for e-commerce sites using Playwright
    
    Note: For production use, you'd need to customize selectors for each site.
    This provides a template structure.
    """
    
    # Common CSS selectors for product elements (customize per site)
    SELECTORS = {
        "product_container": "[data-testid='product'], .product-card, .product-item, article.product",
        "product_name": ".product-name, .product-title, h3, h2",
        "product_price": ".price, .product-price, [data-testid='price']",
        "product_image": "img.product-image, img[data-testid='product-image'], .product-card img",
        "product_link": "a[href*='/product'], a[href*='/item']",
        "rating": ".rating, .stars, [data-testid='rating']",
        "reviews": ".review-count, .reviews, [data-testid='reviews']",
    }
    
    async def scrape(
        self, 
        url: str, 
        max_items: int = 20,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """
        Scrape fashion items from a generic e-commerce site
        
        For demo purposes, falls back to mock data if Playwright isn't available
        or if scraping fails.
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available, using mock scraper")
            from .mock import MockScraper
            mock = MockScraper()
            return await mock.scrape(url, max_items, category_filter)
        
        items = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set a realistic user agent
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                
                await page.goto(url, timeout=self.timeout)
                await page.wait_for_load_state("networkidle")
                
                # Try to find product elements
                products = await page.query_selector_all(self.SELECTORS["product_container"])
                
                for i, product in enumerate(products[:max_items]):
                    try:
                        item = await self._extract_item(product, url, i)
                        if item:
                            # Apply category filter if specified
                            if category_filter is None or item.category == category_filter:
                                items.append(item)
                    except Exception as e:
                        print(f"Error extracting product {i}: {e}")
                        continue
                
                await browser.close()
                
        except Exception as e:
            print(f"Scraping failed: {e}, falling back to mock data")
            from .mock import MockScraper
            mock = MockScraper()
            return await mock.scrape(url, max_items, category_filter)
        
        # If no items found, use mock data
        if not items:
            print("No items found, using mock data")
            from .mock import MockScraper
            mock = MockScraper()
            return await mock.scrape(url, max_items, category_filter)
        
        return items
    
    async def _extract_item(self, element, base_url: str, index: int) -> Optional[FashionItem]:
        """Extract a fashion item from a product element"""
        try:
            # Extract name
            name_el = await element.query_selector(self.SELECTORS["product_name"])
            name = await name_el.inner_text() if name_el else f"Product {index + 1}"
            
            # Extract price
            price_el = await element.query_selector(self.SELECTORS["product_price"])
            price_text = await price_el.inner_text() if price_el else "0"
            price = self._parse_price(price_text)
            
            # Extract image URL
            img_el = await element.query_selector("img")
            image_url = await img_el.get_attribute("src") if img_el else ""
            
            # Extract product link
            link_el = await element.query_selector("a")
            product_url = await link_el.get_attribute("href") if link_el else base_url
            if product_url and not product_url.startswith("http"):
                product_url = base_url.rstrip("/") + "/" + product_url.lstrip("/")
            
            return FashionItem(
                id=str(uuid.uuid4()),
                name=name.strip(),
                price=price,
                currency="USD",
                image_url=image_url,
                product_url=product_url or base_url,
                category=self._guess_category(name),
                brand=self._extract_brand(base_url),
                reviews_count=0,
                rating=0.0,
                sales_count=0,
                trend_score=50.0,
                trend_level=TrendLevel.STABLE,
                colors=[],
                tags=[],
                scraped_at=datetime.now()
            )
        except Exception as e:
            print(f"Error extracting item: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text like '$29.99' or '29.99 USD'"""
        import re
        match = re.search(r'[\d,.]+', price_text.replace(",", ""))
        return float(match.group()) if match else 0.0
    
    def _guess_category(self, name: str) -> FashionCategory:
        """Guess category from product name"""
        name_lower = name.lower()
        
        category_keywords = {
            FashionCategory.DRESS: ["dress", "gown", "maxi", "midi"],
            FashionCategory.TOP: ["top", "shirt", "blouse", "tee", "sweater", "cardigan"],
            FashionCategory.PANTS: ["pants", "jeans", "trousers", "legging"],
            FashionCategory.SKIRT: ["skirt"],
            FashionCategory.JACKET: ["jacket", "blazer", "bomber"],
            FashionCategory.COAT: ["coat", "parka", "trench"],
            FashionCategory.SHOES: ["shoes", "boots", "sneakers", "heels", "sandals"],
            FashionCategory.ACCESSORIES: ["bag", "hat", "scarf", "belt", "jewelry"],
            FashionCategory.SWIMWEAR: ["bikini", "swimsuit", "swimwear"],
            FashionCategory.ACTIVEWEAR: ["yoga", "sports", "athletic", "workout"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in name_lower for kw in keywords):
                return category
        
        return FashionCategory.TOP  # Default
    
    def _extract_brand(self, url: str) -> str:
        """Extract brand name from URL"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove www. and .com/.net/etc
        brand = domain.replace("www.", "").split(".")[0]
        return brand.title()
    
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
