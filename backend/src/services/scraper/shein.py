"""
SHEIN-specific scraper using Playwright

SHEIN uses dynamic JavaScript rendering, so we need Playwright.
This scraper handles SHEIN's specific HTML structure.
"""
import asyncio
import aiohttp
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid
import json

from .base import BaseScraper
from src.models.schemas import FashionItem, FashionCategory, TrendLevel

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class SheinScraper(BaseScraper):
    """
    Scraper specifically designed for SHEIN.com
    
    SHEIN product pages typically have:
    - Product grid with class 'S-product-item' or similar
    - Lazy-loaded images
    - Price in data attributes or specific spans
    - Reviews and ratings in product cards
    """
    
    # SHEIN-specific selectors (may need updates as site changes)
    SELECTORS = {
        # Product grid containers
        "product_grid": ".S-product-item, .product-list-item, [data-sku]",
        "product_card": ".S-product-item__wrapper, .product-card",
        
        # Product details
        "product_name": ".S-product-item__name, .product-item-name, .goods-title-link",
        "product_link": "a.S-product-item__img-container, a.goods-title-link, .product-item a",
        
        # Pricing
        "current_price": ".S-product-item__price, .product-item-price, .normal-price",
        "original_price": ".S-product-item__price-del, .product-item-price-del, .del-price",
        
        # Images
        "product_image": "img.S-product-item__img, img.goods-img, .product-item img",
        
        # Metrics
        "rating": ".S-product-item__star, .star-icon-container, .rating-stars",
        "reviews": ".S-product-item__review, .review-count",
        "sold_count": ".S-product-item__sold, .sold-num",
    }
    
    # Category URL patterns
    CATEGORY_PATTERNS = {
        FashionCategory.DRESS: ["dress", "dresses", "gown"],
        FashionCategory.TOP: ["top", "tops", "blouse", "shirt", "tee", "sweater"],
        FashionCategory.PANTS: ["pants", "jeans", "trousers", "leggings"],
        FashionCategory.SKIRT: ["skirt", "skirts"],
        FashionCategory.JACKET: ["jacket", "jackets", "blazer"],
        FashionCategory.COAT: ["coat", "coats", "outerwear"],
        FashionCategory.SHOES: ["shoes", "boots", "heels", "sneakers", "sandals"],
        FashionCategory.ACCESSORIES: ["accessories", "bag", "bags", "jewelry", "hat"],
        FashionCategory.SWIMWEAR: ["swimwear", "bikini", "swimsuit"],
        FashionCategory.ACTIVEWEAR: ["activewear", "sports", "athletic", "yoga"],
    }
    
    async def scrape(
        self,
        url: str,
        max_items: int = 20,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """
        Scrape fashion items from SHEIN
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is required for SHEIN scraping. Install with: pip install playwright && playwright install chromium")
        
        items = []
        
        try:
            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                )
                
                page = await context.new_page()
                
                # Navigate with retry logic
                await self._navigate_with_retry(page, url)
                
                # Wait for products to load
                await self._wait_for_products(page)
                
                # Scroll to load more items (lazy loading)
                await self._scroll_for_items(page, max_items)
                
                # Extract items
                items = await self._extract_all_items(page, url, max_items, category_filter)
                
                await browser.close()
                
        except Exception as e:
            print(f"SHEIN scraping error: {e}")
            raise
        
        return items
    
    async def _navigate_with_retry(self, page: Page, url: str, max_retries: int = 3):
        """Navigate to URL with retry logic"""
        for attempt in range(max_retries):
            try:
                await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
                await asyncio.sleep(2)  # Wait for JS to initialize
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Navigation attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2)
    
    async def _wait_for_products(self, page: Page):
        """Wait for product grid to load"""
        selectors_to_try = [
            ".S-product-item",
            ".product-list-item", 
            "[data-sku]",
            ".goods-list-item",
            ".product-card"
        ]
        
        for selector in selectors_to_try:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                return
            except:
                continue
        
        print("Warning: Could not find product grid, proceeding anyway...")
    
    async def _scroll_for_items(self, page: Page, target_items: int):
        """Scroll page to trigger lazy loading"""
        items_found = 0
        max_scrolls = 10
        
        for i in range(max_scrolls):
            # Count current items
            items = await page.query_selector_all(self.SELECTORS["product_grid"])
            items_found = len(items)
            
            if items_found >= target_items:
                break
            
            # Scroll down
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(1)
        
        return items_found
    
    async def _extract_all_items(
        self, 
        page: Page, 
        base_url: str, 
        max_items: int,
        category_filter: Optional[FashionCategory]
    ) -> List[FashionItem]:
        """Extract all items from the page"""
        items = []
        
        # Try multiple selectors
        product_elements = await page.query_selector_all(self.SELECTORS["product_grid"])
        
        if not product_elements:
            # Try alternative selectors
            for selector in [".product-list-item", ".goods-list-item", "[data-sku]"]:
                product_elements = await page.query_selector_all(selector)
                if product_elements:
                    break
        
        # Detect category from URL
        detected_category = self._detect_category_from_url(base_url)
        
        for i, element in enumerate(product_elements[:max_items]):
            try:
                item = await self._extract_single_item(element, base_url, i)
                if item:
                    # Override category if detected from URL
                    if detected_category:
                        item.category = detected_category
                    
                    # Apply filter
                    if category_filter is None or item.category == category_filter:
                        items.append(item)
            except Exception as e:
                print(f"Error extracting item {i}: {e}")
                continue
        
        # Sort by trend score
        items.sort(key=lambda x: x.trend_score, reverse=True)
        
        return items
    
    async def _extract_single_item(self, element, base_url: str, index: int) -> Optional[FashionItem]:
        """Extract a single fashion item"""
        try:
            # Name
            name = await self._get_text(element, self.SELECTORS["product_name"])
            if not name:
                name = f"SHEIN Product {index + 1}"
            
            # Price
            price_text = await self._get_text(element, self.SELECTORS["current_price"])
            price = self._parse_price(price_text)
            
            # Original price (if on sale)
            original_price_text = await self._get_text(element, self.SELECTORS["original_price"])
            original_price = self._parse_price(original_price_text) if original_price_text else None
            
            # Image URL
            image_url = await self._get_image_url(element)
            
            # Product URL
            product_url = await self._get_link_url(element, base_url)
            
            # Reviews and rating
            reviews_text = await self._get_text(element, self.SELECTORS["reviews"])
            reviews_count = self._parse_number(reviews_text)
            
            rating = await self._get_rating(element)
            
            # Sales count
            sold_text = await self._get_text(element, self.SELECTORS["sold_count"])
            sales_count = self._parse_number(sold_text)
            
            # Create item
            item = FashionItem(
                id=str(uuid.uuid4()),
                name=name.strip()[:100],  # Limit length
                price=price,
                currency="USD",
                original_price=original_price if original_price and original_price > price else None,
                image_url=image_url,
                product_url=product_url,
                category=self._guess_category(name),
                brand="SHEIN",
                reviews_count=reviews_count,
                rating=rating,
                sales_count=sales_count,
                colors=[],
                tags=self._extract_tags(name),
                scraped_at=datetime.now()
            )
            
            # Calculate trend score
            item.trend_score = self.calculate_trend_score(item)
            item.trend_level = self._get_trend_level(item.trend_score)
            
            return item
            
        except Exception as e:
            print(f"Error extracting item: {e}")
            return None
    
    async def _get_text(self, element, selector: str) -> str:
        """Get text content from a selector"""
        try:
            el = await element.query_selector(selector)
            if el:
                return await el.inner_text()
        except:
            pass
        return ""
    
    async def _get_image_url(self, element) -> str:
        """Extract image URL, handling lazy loading"""
        try:
            img = await element.query_selector("img")
            if img:
                # Try different attributes (lazy loading)
                for attr in ["src", "data-src", "data-lazy-src", "data-original"]:
                    url = await img.get_attribute(attr)
                    if url and url.startswith("http"):
                        return url
        except:
            pass
        return ""
    
    async def _get_link_url(self, element, base_url: str) -> str:
        """Extract product link URL"""
        try:
            link = await element.query_selector("a")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        return href
                    elif href.startswith("/"):
                        # Extract base domain
                        from urllib.parse import urlparse
                        parsed = urlparse(base_url)
                        return f"{parsed.scheme}://{parsed.netloc}{href}"
        except:
            pass
        return base_url
    
    async def _get_rating(self, element) -> float:
        """Extract rating value"""
        try:
            rating_el = await element.query_selector(self.SELECTORS["rating"])
            if rating_el:
                # Try to get from style width (star rating)
                style = await rating_el.get_attribute("style")
                if style:
                    match = re.search(r'width:\s*([\d.]+)%', style)
                    if match:
                        return round(float(match.group(1)) / 20, 1)  # Convert to 5-star scale
                
                # Try to get from text
                text = await rating_el.inner_text()
                match = re.search(r'([\d.]+)', text)
                if match:
                    return min(float(match.group(1)), 5.0)
        except:
            pass
        return 0.0
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        if not price_text:
            return 0.0
        match = re.search(r'[\d,.]+', price_text.replace(",", ""))
        return float(match.group()) if match else 0.0
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text like '1.2k' or '1,234'"""
        if not text:
            return 0
        text = text.lower().replace(",", "")
        
        # Handle k suffix (thousands)
        if "k" in text:
            match = re.search(r'([\d.]+)k', text)
            if match:
                return int(float(match.group(1)) * 1000)
        
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0
    
    def _detect_category_from_url(self, url: str) -> Optional[FashionCategory]:
        """Detect category from URL path"""
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
        return FashionCategory.TOP  # Default
    
    def _extract_tags(self, name: str) -> List[str]:
        """Extract tags from product name"""
        tags = []
        name_lower = name.lower()
        
        tag_keywords = [
            "casual", "elegant", "vintage", "boho", "minimalist",
            "floral", "striped", "solid", "printed", "lace",
            "summer", "winter", "spring", "fall",
            "party", "office", "beach", "workout",
            "plus size", "petite", "maternity"
        ]
        
        for keyword in tag_keywords:
            if keyword in name_lower:
                tags.append(keyword)
        
        return tags[:5]  # Limit to 5 tags
    
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
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
                async with session.get(image_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(content)
                        return True
        except Exception as e:
            print(f"Error downloading image: {e}")
        return False
