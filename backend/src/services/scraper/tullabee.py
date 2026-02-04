"""
Tullabee Scraper using Playwright

Tullabee uses Cloudflare protection, so we need browser-based scraping.
"""
import asyncio
import aiohttp
import re
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .base import BaseScraper
from src.models.schemas import FashionItem, FashionCategory, TrendLevel

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TullabeeScraper(BaseScraper):
    """
    Scraper specifically designed for Tullabee.com
    
    Tullabee is a Shopify store but has Cloudflare protection,
    so we need to use Playwright to bypass it.
    """
    
    BASE_URL = "https://tullabee.com"
    
    SELECTORS = {
        "product_grid": ".product-card, .product-item, [data-product-id], .grid__item",
        "product_name": ".product-card__title, .product__title, .card__heading a",
        "product_link": "a.product-card__link, a.full-unstyled-link, .card__heading a",
        "product_price": ".price-item, .price__regular, .money",
        "product_image": ".product-card__image img, .card__media img, .product__media img",
        "collection_link": "a[href*='/collections/']",
    }
    
    CATEGORY_PATTERNS = {
        FashionCategory.DRESS: ["dress", "dresses", "romper"],
        FashionCategory.TOP: ["top", "tops", "shirt", "blouse", "tee", "sweater"],
        FashionCategory.PANTS: ["pants", "shorts", "leggings", "joggers"],
        FashionCategory.SKIRT: ["skirt", "skirts"],
        FashionCategory.JACKET: ["jacket", "cardigan", "hoodie"],
        FashionCategory.ACCESSORIES: ["accessories", "bow", "headband", "hat"],
        FashionCategory.SHOES: ["shoes", "boots", "sneakers", "sandals"],
    }
    
    async def scrape(
        self,
        url: str = None,
        max_items: int = 200,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """Scrape fashion items from Tullabee"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        
        if url is None:
            url = f"{self.BASE_URL}/collections/all"
        
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
                
                print(f"[TullabeeScraper] Navigating to {url}")
                
                # Navigate and wait for Cloudflare
                await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
                await asyncio.sleep(5)  # Wait for Cloudflare challenge
                
                # Check if we passed Cloudflare
                content = await page.content()
                if "Just a moment" in content or "challenge" in content.lower():
                    print("[TullabeeScraper] Waiting for Cloudflare challenge...")
                    await asyncio.sleep(8)
                
                # Scroll to load more items
                await self._scroll_for_items(page, max_items)
                
                # Extract items
                items = await self._extract_all_items(page, url, max_items, category_filter)
                
                await browser.close()
                
        except Exception as e:
            print(f"[TullabeeScraper] Error: {e}")
            raise
        
        print(f"[TullabeeScraper] Found {len(items)} items")
        return items
    
    async def _scroll_for_items(self, page: Page, target_items: int):
        """Scroll to trigger lazy loading and pagination"""
        last_count = 0
        for i in range(15):  # More scrolls for larger datasets
            # Try multiple selectors
            for selector in [".product-card", ".product-item", ".grid__item", "[data-product-id]"]:
                items = await page.query_selector_all(selector)
                if items:
                    break
            
            current_count = len(items) if items else 0
            print(f"[TullabeeScraper] Scroll {i+1}: {current_count} items found")
            
            if current_count >= target_items:
                break
            
            # If no new items loaded, try clicking "Load More" button
            if current_count == last_count and i > 2:
                try:
                    load_more = await page.query_selector('button:has-text("Load More"), .load-more-btn, [data-load-more]')
                    if load_more:
                        await load_more.click()
                        await asyncio.sleep(2)
                except:
                    pass
            
            last_count = current_count
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
        product_elements = []
        for selector in [".product-card", ".product-item", ".grid__item", "[data-product-id]"]:
            product_elements = await page.query_selector_all(selector)
            if product_elements:
                print(f"[TullabeeScraper] Found {len(product_elements)} elements with selector: {selector}")
                break
        
        if not product_elements:
            # Fallback: find all product links
            product_elements = await page.query_selector_all('a[href*="/products/"]')
            print(f"[TullabeeScraper] Fallback: Found {len(product_elements)} product links")
        
        for i, element in enumerate(product_elements[:max_items]):
            try:
                item = await self._extract_single_item(element, i)
                if item:
                    if category_filter is None or item.category == category_filter:
                        items.append(item)
            except Exception as e:
                print(f"[TullabeeScraper] Error extracting item {i}: {e}")
                continue
        
        return items
    
    async def _extract_single_item(self, element, index: int) -> Optional[FashionItem]:
        """Extract a single fashion item"""
        try:
            # Name
            name = ""
            for selector in [".product-card__title", ".card__heading", ".product__title", "h3", "h2", "[class*='title']"]:
                name_el = await element.query_selector(selector)
                if name_el:
                    name = await name_el.inner_text()
                    if name and name.strip():
                        break
            
            if not name or not name.strip():
                # Try getting from link text
                link = await element.query_selector("a")
                if link:
                    name = await link.inner_text()
            
            if not name or not name.strip():
                return None  # Skip items without names
            
            name = name.strip()
            
            # Price
            price = 0.0
            for selector in [".price-item", ".price__regular", ".money", "[class*='price']"]:
                price_el = await element.query_selector(selector)
                if price_el:
                    price_text = await price_el.inner_text()
                    price = self._parse_price(price_text)
                    if price > 0:
                        break
            
            # Image URL
            image_url = await self._get_image_url(element)
            
            # Product URL
            product_url = await self._get_link_url(element)
            
            item = FashionItem(
                id=str(uuid.uuid4()),
                name=name[:100],
                price=price,
                currency="USD",
                image_url=image_url,
                product_url=product_url,
                category=self._guess_category(name),
                brand="Tullabee",
                reviews_count=0,
                rating=0.0,
                sales_count=0,
                colors=self._extract_colors(name),
                tags=self._extract_tags(name),
                scraped_at=datetime.now()
            )
            
            item.trend_score = self.calculate_trend_score(item)
            item.trend_level = self._get_trend_level(item.trend_score)
            
            return item
            
        except Exception as e:
            print(f"[TullabeeScraper] Error extracting item: {e}")
            return None
    
    async def _get_image_url(self, element) -> str:
        """Extract image URL"""
        try:
            img = await element.query_selector("img")
            if img:
                for attr in ["src", "data-src", "srcset", "data-srcset"]:
                    url = await img.get_attribute(attr)
                    if url:
                        # Handle srcset (take first URL)
                        if " " in url:
                            url = url.split()[0]
                        # Handle protocol-relative URLs
                        if url.startswith("//"):
                            url = "https:" + url
                        if url.startswith("http"):
                            return url
        except:
            pass
        return ""
    
    async def _get_link_url(self, element) -> str:
        """Extract product URL"""
        try:
            # Check if element itself is a link
            tag = await element.evaluate("el => el.tagName")
            if tag == "A":
                href = await element.get_attribute("href")
            else:
                link = await element.query_selector("a[href*='/products/']")
                if not link:
                    link = await element.query_selector("a")
                href = await link.get_attribute("href") if link else None
            
            if href:
                if href.startswith("http"):
                    return href
                elif href.startswith("/"):
                    return f"{self.BASE_URL}{href}"
        except:
            pass
        return self.BASE_URL
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        if not price_text:
            return 0.0
        cleaned = re.sub(r'[^\d.,]', '', price_text.replace(",", ""))
        match = re.search(r'[\d.]+', cleaned)
        return float(match.group()) if match else 0.0
    
    def _guess_category(self, name: str) -> FashionCategory:
        """Guess category from product name"""
        name_lower = name.lower()
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(p in name_lower for p in patterns):
                return category
        return FashionCategory.DRESS  # Default for kids clothing
    
    def _extract_colors(self, name: str) -> List[str]:
        """Extract colors from product name"""
        colors = []
        color_keywords = ["pink", "blue", "red", "white", "black", "green", "yellow", 
                         "purple", "gray", "grey", "navy", "cream", "coral", "mint",
                         "lavender", "peach", "rose", "blush", "ivory"]
        name_lower = name.lower()
        for color in color_keywords:
            if color in name_lower:
                colors.append(color.title())
        return colors[:3]
    
    def _extract_tags(self, name: str) -> List[str]:
        """Extract tags from product name"""
        tags = []
        name_lower = name.lower()
        
        keywords = ["floral", "stripe", "striped", "smocked", "ruffled", "bow",
                   "embroidered", "lace", "cotton", "linen", "denim", "knit"]
        
        for kw in keywords:
            if kw in name_lower:
                tags.append(kw.title())
        
        return tags[:5]
    
    def _get_trend_level(self, score: float) -> TrendLevel:
        """Get trend level from score"""
        if score >= 75:
            return TrendLevel.HOT
        elif score >= 50:
            return TrendLevel.RISING
        elif score >= 25:
            return TrendLevel.STABLE
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
            print(f"[TullabeeScraper] Image download error: {e}")
        return False
