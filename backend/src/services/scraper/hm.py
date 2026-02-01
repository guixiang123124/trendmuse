"""
H&M-specific scraper using Playwright

H&M uses a modern e-commerce frontend with product grids.
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


class HMScraper(BaseScraper):
    """
    Scraper specifically designed for HM.com (H&M)
    
    H&M has a relatively clean product grid structure.
    """
    
    # H&M-specific selectors
    SELECTORS = {
        "product_grid": "[data-testid='product-grid-item'], .product-item, article.hm-product-item, li.product-item",
        "product_name": "[data-testid='product-title'], .item-heading a, .product-item-headline",
        "product_link": "a[data-testid='product-link'], .item-link, a.link",
        "current_price": "[data-testid='product-price'], .price-value, .item-price span",
        "original_price": "[data-testid='product-price-original'], .price-regular",
        "product_image": "img[data-testid='product-image'], .item-image img, img.product-item-image",
    }
    
    CATEGORY_PATTERNS = {
        FashionCategory.DRESS: ["dress", "dresses"],
        FashionCategory.TOP: ["top", "tops", "shirt", "blouse", "t-shirt", "sweater", "hoodie", "cardigan"],
        FashionCategory.PANTS: ["pants", "trousers", "jeans", "leggings", "joggers"],
        FashionCategory.SKIRT: ["skirt", "skirts"],
        FashionCategory.JACKET: ["jacket", "jackets", "blazer", "bomber", "denim jacket"],
        FashionCategory.COAT: ["coat", "coats", "parka", "puffer"],
        FashionCategory.SHOES: ["shoes", "boots", "sneakers", "sandals", "heels"],
        FashionCategory.ACCESSORIES: ["accessories", "bag", "bags", "hat", "scarf", "jewelry"],
        FashionCategory.ACTIVEWEAR: ["sport", "activewear", "gym", "yoga", "running"],
        FashionCategory.SWIMWEAR: ["swim", "bikini", "swimsuit"],
    }
    
    async def scrape(
        self,
        url: str,
        max_items: int = 20,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """Scrape fashion items from H&M"""
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
                await asyncio.sleep(2)
                
                # Handle cookie consent
                try:
                    cookie_btn = await page.query_selector('#onetrust-accept-btn-handler, button[id*="accept"], [data-testid="cookie-accept"]')
                    if cookie_btn:
                        await cookie_btn.click()
                        await asyncio.sleep(1)
                except:
                    pass
                
                # Scroll to load items
                await self._scroll_for_items(page, max_items)
                
                # Extract items
                items = await self._extract_all_items(page, url, max_items, category_filter)
                
                await browser.close()
                
        except Exception as e:
            print(f"H&M scraping error: {e}")
            raise
        
        return items
    
    async def _scroll_for_items(self, page: Page, target_items: int):
        """Scroll to load more items"""
        for i in range(10):
            items = await page.query_selector_all(self.SELECTORS["product_grid"])
            if len(items) >= target_items:
                break
            
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(1)
            
            # Try clicking "Load More" button if exists
            try:
                load_more = await page.query_selector('button[data-testid="load-more"], .load-more-button')
                if load_more:
                    await load_more.click()
                    await asyncio.sleep(2)
            except:
                pass
    
    async def _extract_all_items(
        self,
        page: Page,
        base_url: str,
        max_items: int,
        category_filter: Optional[FashionCategory]
    ) -> List[FashionItem]:
        """Extract all items"""
        items = []
        
        product_elements = await page.query_selector_all(self.SELECTORS["product_grid"])
        
        if not product_elements:
            # Try alternatives
            for selector in [".product-item", "article[class*='product']", "li[class*='product']"]:
                product_elements = await page.query_selector_all(selector)
                if product_elements:
                    break
        
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
                print(f"Error extracting H&M item {i}: {e}")
                continue
        
        items.sort(key=lambda x: x.trend_score, reverse=True)
        return items
    
    async def _extract_single_item(self, element, base_url: str, index: int) -> Optional[FashionItem]:
        """Extract a single item"""
        try:
            # Name
            name = ""
            for selector in self.SELECTORS["product_name"].split(", "):
                name_el = await element.query_selector(selector)
                if name_el:
                    name = await name_el.inner_text()
                    if name:
                        break
            
            if not name:
                name = f"H&M Product {index + 1}"
            
            # Price
            price = 0.0
            price_el = await element.query_selector(self.SELECTORS["current_price"])
            if price_el:
                price_text = await price_el.inner_text()
                price = self._parse_price(price_text)
            
            # Original price
            original_price = None
            orig_el = await element.query_selector(self.SELECTORS["original_price"])
            if orig_el:
                orig_text = await orig_el.inner_text()
                original_price = self._parse_price(orig_text)
            
            # Image
            image_url = await self._get_image_url(element)
            
            # Link
            product_url = await self._get_link_url(element, base_url)
            
            item = FashionItem(
                id=str(uuid.uuid4()),
                name=name.strip()[:100],
                price=price,
                currency="USD",
                original_price=original_price if original_price and original_price > price else None,
                image_url=image_url,
                product_url=product_url,
                category=self._guess_category(name),
                brand="H&M",
                reviews_count=0,
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
            print(f"Error: {e}")
            return None
    
    async def _get_image_url(self, element) -> str:
        """Get image URL"""
        try:
            img = await element.query_selector("img")
            if img:
                for attr in ["src", "data-src", "data-srcset", "srcset"]:
                    url = await img.get_attribute(attr)
                    if url:
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
        """Get product link"""
        try:
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
        """Parse price"""
        if not price_text:
            return 0.0
        match = re.search(r'[\d,.]+', price_text.replace(",", "."))
        return float(match.group().replace(",", "")) if match else 0.0
    
    def _detect_category_from_url(self, url: str) -> Optional[FashionCategory]:
        """Detect category from URL"""
        url_lower = url.lower()
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(p in url_lower for p in patterns):
                return category
        return None
    
    def _guess_category(self, name: str) -> FashionCategory:
        """Guess category"""
        name_lower = name.lower()
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(p in name_lower for p in patterns):
                return category
        return FashionCategory.TOP
    
    def _extract_tags(self, name: str) -> List[str]:
        """Extract tags"""
        tags = []
        name_lower = name.lower()
        keywords = ["conscious", "premium", "basic", "oversized", "slim fit", "regular fit",
                   "organic", "recycled", "cotton", "linen", "denim"]
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
        except:
            pass
        return False
