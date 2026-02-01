"""
Base scraper class for fashion e-commerce sites
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.schemas import FashionItem, FashionCategory


class BaseScraper(ABC):
    """Abstract base class for fashion scrapers"""
    
    def __init__(self, timeout: int = 30000):
        self.timeout = timeout
    
    @abstractmethod
    async def scrape(
        self, 
        url: str, 
        max_items: int = 20,
        category_filter: Optional[FashionCategory] = None
    ) -> List[FashionItem]:
        """
        Scrape fashion items from a URL
        
        Args:
            url: The website URL to scrape
            max_items: Maximum number of items to return
            category_filter: Optional category to filter by
            
        Returns:
            List of FashionItem objects
        """
        pass
    
    @abstractmethod
    async def download_image(self, image_url: str, save_path: str) -> bool:
        """
        Download an image from URL
        
        Args:
            image_url: URL of the image
            save_path: Local path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def calculate_trend_score(self, item: FashionItem) -> float:
        """
        Calculate a trend score based on reviews, rating, and sales
        
        Args:
            item: The fashion item to score
            
        Returns:
            Trend score from 0-100
        """
        # Weight factors
        review_weight = 0.3
        rating_weight = 0.3
        sales_weight = 0.4
        
        # Normalize values
        review_score = min(item.reviews_count / 1000, 1.0) * 100
        rating_score = (item.rating / 5.0) * 100
        sales_score = min(item.sales_count / 5000, 1.0) * 100
        
        # Calculate weighted score
        score = (
            review_score * review_weight +
            rating_score * rating_weight +
            sales_score * sales_weight
        )
        
        return round(score, 1)
