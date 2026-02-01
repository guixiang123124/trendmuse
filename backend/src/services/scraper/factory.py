"""
Scraper Factory

Automatically selects the appropriate scraper based on URL.
"""
from typing import Optional
from urllib.parse import urlparse

from .base import BaseScraper
from .mock import MockScraper
from .generic import GenericScraper
from .shein import SheinScraper
from .zara import ZaraScraper
from .hm import HMScraper


class ScraperFactory:
    """
    Factory to create the appropriate scraper based on URL
    """
    
    # Map of domain patterns to scraper classes
    SCRAPER_MAP = {
        # SHEIN
        "shein": SheinScraper,
        "us.shein": SheinScraper,
        "m.shein": SheinScraper,
        # ZARA
        "zara": ZaraScraper,
        # H&M
        "hm.com": HMScraper,
        "www2.hm": HMScraper,
        "h&m": HMScraper,
    }
    
    @classmethod
    def get_scraper(cls, url: str, demo_mode: bool = False, timeout: int = 30000) -> BaseScraper:
        """
        Get the appropriate scraper for a given URL
        
        Args:
            url: The URL to scrape
            demo_mode: If True, always return MockScraper
            timeout: Request timeout in milliseconds
            
        Returns:
            An instance of the appropriate scraper
        """
        if demo_mode:
            return MockScraper(timeout=timeout)
        
        # Extract domain from URL
        domain = cls._extract_domain(url)
        
        # Find matching scraper
        for pattern, scraper_class in cls.SCRAPER_MAP.items():
            if pattern in domain.lower():
                print(f"Using {scraper_class.__name__} for {domain}")
                return scraper_class(timeout=timeout)
        
        # Fall back to generic scraper
        print(f"Using GenericScraper for {domain}")
        return GenericScraper(timeout=timeout)
    
    @classmethod
    def _extract_domain(cls, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    @classmethod
    def get_supported_sites(cls) -> list:
        """Get list of sites with dedicated scrapers"""
        sites = []
        for domain, scraper in cls.SCRAPER_MAP.items():
            if domain not in sites:
                sites.append({
                    "domain": domain,
                    "scraper": scraper.__name__,
                    "status": "supported"
                })
        return sites
