"""
Lilly Pulitzer Scraper using Playwright

Lilly Pulitzer uses Salesforce Commerce Cloud (Demandware).
Requires browser-based scraping.
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


class LillyPulitzerScraper(BaseScraper):
    """
    Scraper specifically designed for LillyPulitzer.com
    
    Lilly Pulitzer uses Salesforce Commerce Cloud (Demandware).
    Known for colorful resort wear and preppy style.
    """
    
    BASE_URL = "https://www.lillypulitzer.com"
    
    SELECTORS = {
        "product_tile": ".product-tile, .product, [data-product-tile], .product-grid-item",
        "product_name": ".product-tile__name, .product-name, .pdp-link a, .link",
        "product_link": ".product-tile__link, a.link, .pdp-link a, .product-tile a",
        "product_price": ".product-tile__price, .price .value, .sales .value, [data-product-price]",
        "product_image": ".product-tile__image img, .tile-image, img.product-image",
        "load_more": ".show-more button, .load-more, [data-load-more]",
    }
    
    CATEGORY_PATTERNS = {
        FashionCategory.DRESS: ["dress", "dresses", "romper", "jumpsuit"],
        FashionCategory.TOP: ["top", "tops", "shirt", "blouse", "tee", "sweater", "tank", "tunic"],
        FashionCategory.PANTS: ["pants", "shorts", "capri", "joggers", "leggings"],
        FashionCategory.SKIRT: ["skirt", "skirts", "skort"],
        FashionCategory.JACKET: ["jacket", "cardigan", "pullover", "hoodie"],
        FashionCategory.COAT: ["coat", "outerwear"],
        FashionCategory.SHOES: ["shoes", "sandals", "sneakers", "flip flops", "slides"],
        FashionCategory.ACCESSORIES: ["accessories", "bag", "tote", "scarf", "hat", "jewelry"],
    }
    
    # Collection URLs for different categories
    COLLECTIONS = {
        "new-arrivals": "/new-arrivals/",
        "dresses": "/women/dresses/",
        "tops": "/women/tops/",
        "bottoms": "/women/bottoms/",
        "swim": "/women/swim/",
        "girls": "/girls/",
        "accessories": "/accessories/",
    }
    
    async def scrape(
        self,
        url: str = None,
        max_items: int = 200,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """Scrape fashion items from Lilly Pulitzer"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        
        if url is None:
            url = f"{self.BASE_URL}/new-arrivals/"
        
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
                
                print(f"[LillyPulitzerScraper] Navigating to {url}")
                
                # Navigate
                await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
                await asyncio.sleep(3)
                
                # Close any popup modals
                await self._close_popups(page)
                
                # Scroll to load more items
                await self._scroll_for_items(page, max_items)
                
                # Extract items
                items = await self._extract_all_items(page, url, max_items, category_filter)
                
                await browser.close()
                
        except Exception as e:
            print(f"[LillyPulitzerScraper] Error: {e}")
            raise
        
        print(f"[LillyPulitzerScraper] Found {len(items)} items")
        return items
    
    async def scrape_all_categories(self, max_items_per_category: int = 50) -> List[FashionItem]:
        """Scrape from multiple categories"""
        all_items = []
        
        for name, path in self.COLLECTIONS.items():
            try:
                print(f"[LillyPulitzerScraper] Scraping category: {name}")
                url = f"{self.BASE_URL}{path}"
                items = await self.scrape(url, max_items=max_items_per_category)
                all_items.extend(items)
            except Exception as e:
                print(f"[LillyPulitzerScraper] Error scraping {name}: {e}")
                continue
        
        # Deduplicate by product URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            if item.product_url not in seen_urls:
                seen_urls.add(item.product_url)
                unique_items.append(item)
        
        return unique_items
    
    async def _close_popups(self, page: Page):
        """Close any modal popups"""
        try:
            # Common popup close selectors
            for selector in [
                'button[aria-label="Close"]',
                '.modal-close',
                '.close-button',
                '[data-dismiss="modal"]',
                '.email-modal button.close',
                '#emailModal .close',
            ]:
                close_btn = await page.query_selector(selector)
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(0.5)
        except:
            pass
    
    async def _scroll_for_items(self, page: Page, target_items: int):
        """Scroll and click load more to get more items"""
        last_count = 0
        
        for i in range(20):  # More iterations for larger datasets
            # Count current items
            product_elements = await page.query_selector_all('.product-tile, .product, [data-product-tile]')
            current_count = len(product_elements)
            
            print(f"[LillyPulitzerScraper] Scroll {i+1}: {current_count} items found")
            
            if current_count >= target_items:
                break
            
            # Try clicking "Show More" / "Load More" button
            if current_count == last_count or i % 3 == 0:
                try:
                    for btn_selector in [
                        '.show-more button',
                        'button.show-more',
                        '.load-more-btn',
                        '[data-load-more]',
                        'button:has-text("Show More")',
                        'button:has-text("Load More")',
                    ]:
                        load_more = await page.query_selector(btn_selector)
                        if load_more and await load_more.is_visible():
                            await load_more.click()
                            await asyncio.sleep(2)
                            break
                except:
                    pass
            
            last_count = current_count
            
            # Scroll down
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
        for selector in ['.product-tile', '.product', '[data-product-tile]', '.product-grid-item']:
            product_elements = await page.query_selector_all(selector)
            if product_elements:
                print(f"[LillyPulitzerScraper] Found {len(product_elements)} elements with selector: {selector}")
                break
        
        if not product_elements:
            # Fallback: find all product links
            product_elements = await page.query_selector_all('a[href*="/product/"]')
            print(f"[LillyPulitzerScraper] Fallback: Found {len(product_elements)} product links")
        
        detected_category = self._detect_category_from_url(base_url)
        
        for i, element in enumerate(product_elements[:max_items]):
            try:
                item = await self._extract_single_item(element, i)
                if item:
                    if detected_category:
                        item.category = detected_category
                    
                    if category_filter is None or item.category == category_filter:
                        items.append(item)
            except Exception as e:
                print(f"[LillyPulitzerScraper] Error extracting item {i}: {e}")
                continue
        
        return items
    
    async def _extract_single_item(self, element, index: int) -> Optional[FashionItem]:
        """Extract a single fashion item"""
        try:
            # Name
            name = ""
            for selector in ['.product-tile__name', '.product-name', '.pdp-link', '.link', 'a']:
                name_el = await element.query_selector(selector)
                if name_el:
                    name = await name_el.inner_text()
                    if name and name.strip() and len(name.strip()) > 3:
                        break
            
            if not name or not name.strip():
                return None
            
            name = name.strip().split('\n')[0]  # Take first line only
            
            # Price
            price = 0.0
            for selector in ['.price .value', '.sales .value', '.product-tile__price', '[data-product-price]', '.price']:
                price_el = await element.query_selector(selector)
                if price_el:
                    price_text = await price_el.inner_text()
                    price = self._parse_price(price_text)
                    if price > 0:
                        break
            
            # Original price (if on sale)
            original_price = None
            for selector in ['.strike-through .value', '.list-price .value']:
                orig_el = await element.query_selector(selector)
                if orig_el:
                    orig_text = await orig_el.inner_text()
                    orig = self._parse_price(orig_text)
                    if orig > price:
                        original_price = orig
                        break
            
            # Image URL
            image_url = await self._get_image_url(element)
            
            # Product URL
            product_url = await self._get_link_url(element)
            
            item = FashionItem(
                id=str(uuid.uuid4()),
                name=name[:100],
                price=price,
                original_price=original_price,
                currency="USD",
                image_url=image_url,
                product_url=product_url,
                category=self._guess_category(name),
                brand="Lilly Pulitzer",
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
            print(f"[LillyPulitzerScraper] Error extracting item: {e}")
            return None
    
    async def _get_image_url(self, element) -> str:
        """Extract image URL"""
        try:
            img = await element.query_selector("img")
            if img:
                for attr in ["src", "data-src", "srcset", "data-srcset"]:
                    url = await img.get_attribute(attr)
                    if url:
                        if " " in url:
                            url = url.split()[0]
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
            link = await element.query_selector("a[href*='/product/'], a.pdp-link, a.link, a")
            if link:
                href = await link.get_attribute("href")
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
        return FashionCategory.DRESS  # Default for Lilly Pulitzer
    
    def _extract_colors(self, name: str) -> List[str]:
        """Extract colors from product name - Lilly Pulitzer has unique print names"""
        colors = []
        # Standard colors
        color_keywords = ["pink", "blue", "green", "yellow", "white", "navy", "coral", 
                         "turquoise", "gold", "purple", "orange", "red", "black"]
        name_lower = name.lower()
        for color in color_keywords:
            if color in name_lower:
                colors.append(color.title())
        return colors[:3]
    
    def _extract_tags(self, name: str) -> List[str]:
        """Extract tags from product name"""
        tags = []
        name_lower = name.lower()
        
        # Lilly Pulitzer specific keywords
        keywords = ["upf", "linen", "cotton", "silk", "jersey", "ponte",
                   "shift", "maxi", "midi", "mini", "halter", "strapless",
                   "printed", "solid", "striped", "scalloped", "embroidered",
                   "gold buttons", "pockets", "tiered", "pleated"]
        
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
            print(f"[LillyPulitzerScraper] Image download error: {e}")
        return False
