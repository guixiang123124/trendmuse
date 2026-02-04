"""
TrendMuse Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "TrendMuse"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    images_dir: Path = data_dir / "images"
    sketches_dir: Path = data_dir / "sketches"
    generated_dir: Path = data_dir / "generated"
    
    # API Keys (optional - demo mode without them)
    replicate_api_token: str | None = None
    
    # GrsAI API (Nano Banana image generation)
    grsai_api_key: str | None = None
    grsai_api_base: str = "https://api.grsai.com"
    grsai_model: str = "nano-banana-fast"  # or "nano-banana-pro"
    
    # Scraping settings
    scrape_timeout: int = 30000  # ms
    max_items_per_scan: int = 50
    
    # Demo mode
    demo_mode: bool = True  # Set to False when API keys are configured
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.sketches_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect demo mode
        if self.replicate_api_token or self.grsai_api_key:
            self.demo_mode = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
