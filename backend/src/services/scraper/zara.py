"""
ZARA-specific scraper using Playwright

ZARA uses a modern React-based frontend with dynamic loading.
"""
import asyncio
import aiohttp
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from .base import BaseScraper
from src.models.schemas import FashionItem, FashionCategory, TrendLevel

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ZaraScraper(BaseScraper):
    """
    Scraper specifically designed for ZARA.com
    
    ZARA uses a React-based SPA with specific data structures.
    Products are often in grid layouts with lazy-loaded images.
    """
    
    # ZARA-specific selectors
    SELECTORS = {
        "product_grid": ".product-grid__product, .product-grid-product, [data-productid], .product-link",
        "product_name": ".product-grid-product-info__name, .product-link__name, .product-name",
        "product_link": "a.product-link, a[href*='/p/']",
        "current_price": ".money-amount__main, .price__amount, .product-price",
        "original_price": ".price__amount--old, .money-amount__main--old",
        "product_image": "img.media-image__image, img[data-srcset], .product-image img",
    }
    
    CATEGORY_PATTERNS = {
        FashionCategory.DRESS: ["dress", "dresses", "vestido"],
        FashionCategory.TOP: ["top", "tops", "shirt", "blouse", "tee", "sweater", "knitwear"],
        FashionCategory.PANTS: ["pants", "trousers", "jeans", "leggings"],
        FashionCategory.SKIRT: ["skirt", "skirts"],
        FashionCategory.JACKET: ["jacket", "jackets", "blazer", "bomber"],
        FashionCategory.COAT: ["coat", "coats", "outerwear", "parka"],
        FashionCategory.SHOES: ["shoes", "boots", "heels", "sneakers", "sandals", "footwear"],
        FashionCategory.ACCESSORIES: ["accessories", "bag", "bags", "scarf", "belt", "jewelry"],
    }
    
    async def scrape(
        self,
        url: str,
        max_items: int = 20,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """Scrape fashion items from ZARA"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        
        items = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                )
                
                page = await context.new_page()
                
                # Navigate
                await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
                await asyncio.sleep(3)  # Wait for React to render
                
                # Accept cookies if dialog appears
                try:
                    cookie_btn = await page.query_selector('#onetrust-accept-btn-handler, [data-qa="cookies-accept"]')
                    if cookie_btn:
                        await cookie_btn.click()
                        await asyncio.sleep(1)
                except:
                    pass
                
                # Scroll to load more items
                await self._scroll_for_items(page, max_items)
                
                # Extract items
                items = await self._extract_all_items(page, url, max_items, category_filter)
                
                await browser.close()
                
        except Exception as e:
            print(f"ZARA scraping error: {e}")
            raise
        
        return items
    
    async def _scroll_for_items(self, page: Page, target_items: int):
        """Scroll to trigger lazy loading"""
        for i in range(8):
            items = await page.query_selector_all(self.SELECTORS["product_grid"])
            if len(items) >= target_items:
                break
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(1.5)
    
    async def _extract_all_items(
        self,
        page: Page,
        base_url: str,
        max_items: int,
        category_filter: Optional[FashionCategory]
    ) -> List[FashionItem]:
        """Extract all items from page"""
        items = []
        
        # Try multiple selector strategies
        product_elements = await page.query_selector_all(self.SELECTORS["product_grid"])
        
        if not product_elements:
            # Try alternative: get all product links
            product_elements = await page.query_selector_all('a[href*="/p/"], .product-link')
        
        detected_category = self._detect_category_from_url(base_url)
        
        for i, element in enumerate(product_elements[:max_items]):
            try:
                item = await self._extract_single_item(element, base_url, i)
                if item:
                    if detected_category:
                        item.category = detected_category
                    
                    if category_filter is None or item.category == category_filter:
                        items.append(item)
            except Exception as e:
                print(f"Error extracting ZARA item {i}: {e}")
                continue
        
        items.sort(key=lambda x: x.trend_score, reverse=True)
        return items
    
    async def _extract_single_item(self, element, base_url: str, index: int) -> Optional[FashionItem]:
        """Extract a single fashion item"""
        try:
            # Name
            name = ""
            for selector in [".product-grid-product-info__name", ".product-link__name", "h2", "[class*='name']"]:
                name_el = await element.query_selector(selector)
                if name_el:
                    name = await name_el.inner_text()
                    if name:
                        break
            
            if not name:
                name = f"ZARA Product {index + 1}"
            
            # Price
            price = 0.0
            for selector in [".money-amount__main", ".price__amount", "[class*='price']"]:
                price_el = await element.query_selector(selector)
                if price_el:
                    price_text = await price_el.inner_text()
                    price = self._parse_price(price_text)
                    if price > 0:
                        break
            
            # Image URL
            image_url = await self._get_image_url(element)
            
            # Product URL
            product_url = await self._get_link_url(element, base_url)
            
            item = FashionItem(
                id=str(uuid.uuid4()),
                name=name.strip()[:100],
                price=price,
                currency="USD",
                image_url=image_url,
                product_url=product_url,
                category=self._guess_category(name),
                brand="ZARA",
                reviews_count=0,  # ZARA doesn't show reviews
                rating=0.0,
                sales_count=0,
                colors=[],
                tags=self._extract_tags(name),
                scraped_at=datetime.now()
            )
            
            item.trend_score = self.calculate_trend_score(item)
            item.trend_level = self._get_trend_level(item.trend_score)
            
            return item
            
        except Exception as e:
            print(f"Error extracting ZARA item: {e}")
            return None
    
    async def _get_image_url(self, element) -> str:
        """Extract image URL"""
        try:
            img = await element.query_selector("img")
            if img:
                for attr in ["src", "data-src", "srcset"]:
                    url = await img.get_attribute(attr)
                    if url:
                        # Handle srcset (take first URL)
                        if " " in url:
                            url = url.split()[0]
                        if url.startswith("http"):
                            return url
                        elif url.startswith("//"):
                            return "https:" + url
        except:
            pass
        return ""
    
    async def _get_link_url(self, element, base_url: str) -> str:
        """Extract product URL"""
        try:
            # Check if element itself is a link
            href = await element.get_attribute("href")
            if href:
                if href.startswith("http"):
                    return href
                elif href.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    return f"{parsed.scheme}://{parsed.netloc}{href}"
            
            # Otherwise find link inside
            link = await element.query_selector("a")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        return href
                    elif href.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(base_url)
                        return f"{parsed.scheme}://{parsed.netloc}{href}"
        except:
            pass
        return base_url
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        if not price_text:
            return 0.0
        # Remove currency symbols and clean
        cleaned = re.sub(r'[^\d.,]', '', price_text.replace(",", "."))
        match = re.search(r'[\d.]+', cleaned)
        return float(match.group()) if match else 0.0
    
    def _detect_category_from_url(self, url: str) -> Optional[FashionCategory]:
        """Detect category from URL"""
        url_lower = url.lower()
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(p in url_lower for p in patterns):
                return category
        return None
    
    def _guess_category(self, name: str) -> FashionCategory:
        """Guess category from product name"""
        name_lower = name.lower()
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(p in name_lower for p in patterns):
                return category
        return FashionCategory.TOP
    
    def _extract_tags(self, name: str) -> List[str]:
        """Extract tags from product name"""
        tags = []
        name_lower = name.lower()
        
        keywords = ["basic", "premium", "limited", "oversized", "cropped", "fitted",
                   "printed", "striped", "floral", "knit", "satin", "leather", "linen"]
        
        for kw in keywords:
            if kw in name_lower:
                tags.append(kw)
        
        return tags[:5]
    
    def _get_trend_level(self, score: float) -> TrendLevel:
        """Get trend level"""
        if score >= 75:
            return TrendLevel.HOT
        elif score >= 50:
            return TrendLevel.RISING
        elif score >= 25:
            return TrendLevel.STABLE
        return TrendLevel.DECLINING
    
    async def download_image(self, image_url: str, save_path: str) -> bool:
        """Download image"""
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
            print(f"Error downloading: {e}")
        return False
