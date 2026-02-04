"""
Image Generation Service

Generates design variations using AI image generation.
Currently supports:
- Demo mode: Returns placeholder variations
- GrsAI API: Nano Banana (Google Gemini 2.5 Flash Image) - RECOMMENDED
- Replicate API: Alternative option
"""
import uuid
import random
import asyncio
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import aiohttp

from src.models.schemas import (
    FashionItem, 
    GeneratedDesign, 
    GenerationStyle,
    ColorPalette
)
from src.core.config import get_settings

# Replicate import with fallback
try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False


# Placeholder images for demo mode
DEMO_VARIATIONS = [
    "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400",
    "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400",
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400",
    "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400",
    "https://images.unsplash.com/photo-1558171813-4c088753af8f?w=400",
    "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=400",
    "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=400",
]


class ImageGenerationService:
    """
    Service for generating design variations
    
    Supports:
    - GrsAI API (Nano Banana) - Recommended, cheapest option
    - Replicate API - Alternative
    - Demo mode - Placeholder images when no API key
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.demo_mode = self.settings.demo_mode
        self.use_grsai = bool(self.settings.grsai_api_key)
    
    async def generate_variations(
        self,
        source_item: FashionItem,
        style: GenerationStyle,
        variation_strength: float = 0.5,
        color_palette: Optional[ColorPalette] = None,
        num_variations: int = 4,
        prompt_additions: Optional[str] = None
    ) -> List[GeneratedDesign]:
        """
        Generate design variations for a fashion item
        
        Args:
            source_item: The original fashion item
            style: Generation style (minimalist, avant-garde, etc.)
            variation_strength: How different from original (0.1-1.0)
            color_palette: Optional color palette to use
            num_variations: Number of variations to generate
            prompt_additions: Additional prompt text
            
        Returns:
            List of generated design variations
        """
        if self.demo_mode:
            return await self._generate_demo_variations(
                source_item, style, variation_strength, num_variations
            )
        elif self.use_grsai:
            return await self._generate_with_grsai(
                source_item, style, variation_strength, color_palette, 
                num_variations, prompt_additions
            )
        else:
            return await self._generate_with_replicate(
                source_item, style, variation_strength, color_palette, 
                num_variations, prompt_additions
            )
    
    async def _generate_demo_variations(
        self,
        source_item: FashionItem,
        style: GenerationStyle,
        variation_strength: float,
        num_variations: int
    ) -> List[GeneratedDesign]:
        """Generate demo variations using placeholder images"""
        variations = []
        
        for i in range(num_variations):
            design = GeneratedDesign(
                id=str(uuid.uuid4()),
                source_item_id=source_item.id,
                image_url=random.choice(DEMO_VARIATIONS),
                style=style,
                variation_strength=variation_strength,
                generation_prompt=self._build_prompt(source_item, style, None, None),
                created_at=datetime.now()
            )
            variations.append(design)
        
        return variations
    
    async def _generate_with_grsai(
        self,
        source_item: FashionItem,
        style: GenerationStyle,
        variation_strength: float,
        color_palette: Optional[ColorPalette],
        num_variations: int,
        prompt_additions: Optional[str]
    ) -> List[GeneratedDesign]:
        """
        Generate variations using GrsAI API (Nano Banana)
        
        GrsAI provides access to Google's Nano Banana (Gemini 2.5 Flash Image) API
        at much lower prices than official Google pricing.
        """
        variations = []
        prompt = self._build_prompt(source_item, style, color_palette, prompt_additions)
        
        api_base = self.settings.grsai_api_base
        api_key = self.settings.grsai_api_key
        model = self.settings.grsai_model
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                for i in range(num_variations):
                    # Create generation task (synchronous SSE mode)
                    payload = {
                        "model": model,
                        "prompt": prompt,
                        "aspectRatio": "1:1",  # Square for fashion items
                    }
                    
                    # Add reference image if available
                    if source_item.image_url:
                        payload["urls"] = [source_item.image_url]
                    
                    # Send request and process SSE stream
                    image_url = await self._generate_grsai_sse(session, api_base, headers, payload)
                    
                    if image_url:
                        design = GeneratedDesign(
                            id=str(uuid.uuid4()),
                            source_item_id=source_item.id,
                            image_url=image_url,
                            style=style,
                            variation_strength=variation_strength,
                            generation_prompt=prompt,
                            created_at=datetime.now()
                        )
                        variations.append(design)
                        
        except Exception as e:
            print(f"GrsAI generation error: {e}")
            # Fallback to demo mode
            if not variations:
                return await self._generate_demo_variations(
                    source_item, style, variation_strength, num_variations
                )
        
        return variations
    
    async def _generate_grsai_sse(
        self,
        session: aiohttp.ClientSession,
        api_base: str,
        headers: dict,
        payload: dict,
        timeout: int = 120
    ) -> Optional[str]:
        """
        Generate image using GrsAI SSE (Server-Sent Events) stream.
        The API returns progress updates as SSE events until completion.
        """
        import json
        
        try:
            async with session.post(
                f"{api_base}/v1/draw/nano-banana",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"GrsAI API error: {response.status} - {error_text}")
                    return None
                
                # Process SSE stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Parse SSE data line
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            
                            status = data.get("status", "").lower()
                            
                            if status == "succeeded":
                                results = data.get("results", [])
                                if results and results[0].get("url"):
                                    return results[0]["url"]
                            elif status == "failed":
                                failure_reason = data.get("failure_reason", "Unknown")
                                print(f"GrsAI generation failed: {failure_reason}")
                                return None
                            # else: still running, continue reading stream
                            
                        except json.JSONDecodeError:
                            continue
                
        except asyncio.TimeoutError:
            print("GrsAI generation timeout")
        except Exception as e:
            print(f"GrsAI SSE error: {e}")
        
        return None
    
    async def _poll_grsai_result(
        self, 
        session: aiohttp.ClientSession, 
        api_base: str, 
        headers: dict, 
        task_id: str,
        max_attempts: int = 30,
        interval: float = 2.0
    ) -> Optional[str]:
        """Poll GrsAI for task result"""
        for attempt in range(max_attempts):
            await asyncio.sleep(interval)
            
            try:
                # Use POST request with task_id in body
                async with session.post(
                    f"{api_base}/v1/draw/result",
                    headers=headers,
                    json={"task_id": task_id}
                ) as response:
                    if response.status != 200:
                        continue
                    
                    result = await response.json()
                    
                    # Check if result exists
                    if result.get("code") == -22:
                        # Result not ready yet, continue polling
                        continue
                    
                    # Check status field (succeeded/running/failed)
                    status = result.get("status", "").lower()
                    
                    if status == "succeeded":
                        # Get the generated image URL from results array
                        results = result.get("results", [])
                        if results and results[0].get("url"):
                            return results[0]["url"]
                    elif status == "failed":
                        failure_reason = result.get("failure_reason", "Unknown")
                        print(f"GrsAI task failed: {failure_reason}")
                        return None
                    # else: still running, continue polling
                    
            except Exception as e:
                print(f"GrsAI poll error: {e}")
                continue
        
        print(f"GrsAI task timeout: {task_id}")
        return None
    
    async def _generate_with_replicate(
        self,
        source_item: FashionItem,
        style: GenerationStyle,
        variation_strength: float,
        color_palette: Optional[ColorPalette],
        num_variations: int,
        prompt_additions: Optional[str]
    ) -> List[GeneratedDesign]:
        """
        Generate variations using Replicate API
        
        Uses Stable Diffusion XL with img2img for variations.
        
        To enable:
        1. Set REPLICATE_API_TOKEN in .env
        2. Uncomment the generation code below
        """
        variations = []
        prompt = self._build_prompt(source_item, style, color_palette, prompt_additions)
        
        # ============================================================
        # REPLICATE API INTEGRATION (Uncomment when API key is set)
        # ============================================================
        # 
        # try:
        #     for i in range(num_variations):
        #         # Using SDXL img2img model
        #         output = replicate.run(
        #             "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        #             input={
        #                 "prompt": prompt,
        #                 "image": source_item.image_url,
        #                 "strength": variation_strength,
        #                 "num_outputs": 1,
        #                 "guidance_scale": 7.5,
        #                 "negative_prompt": "low quality, blurry, distorted",
        #             }
        #         )
        #         
        #         if output and len(output) > 0:
        #             design = GeneratedDesign(
        #                 id=str(uuid.uuid4()),
        #                 source_item_id=source_item.id,
        #                 image_url=output[0],
        #                 style=style,
        #                 variation_strength=variation_strength,
        #                 generation_prompt=prompt,
        #                 created_at=datetime.now()
        #             )
        #             variations.append(design)
        #             
        # except Exception as e:
        #     print(f"Replicate API error: {e}")
        #     # Fallback to demo mode
        #     return await self._generate_demo_variations(
        #         source_item, style, variation_strength, num_variations
        #     )
        #
        # ============================================================
        
        # For now, fallback to demo mode
        return await self._generate_demo_variations(
            source_item, style, variation_strength, num_variations
        )
    
    def _build_prompt(
        self,
        source_item: FashionItem,
        style: GenerationStyle,
        color_palette: Optional[ColorPalette],
        prompt_additions: Optional[str]
    ) -> str:
        """Build a generation prompt"""
        
        # Style prompts
        style_prompts = {
            GenerationStyle.MINIMALIST: "minimalist, clean lines, simple design, modern",
            GenerationStyle.AVANT_GARDE: "avant-garde, experimental, high fashion, artistic, runway",
            GenerationStyle.BOHEMIAN: "bohemian, flowy, natural, earthy, relaxed",
            GenerationStyle.STREETWEAR: "streetwear, urban, edgy, contemporary, casual cool",
            GenerationStyle.VINTAGE: "vintage, retro, classic, timeless, nostalgic",
            GenerationStyle.FUTURISTIC: "futuristic, metallic, innovative, tech-inspired, modern",
        }
        
        # Base prompt
        prompt_parts = [
            "fashion design",
            source_item.category.value,
            style_prompts.get(style, ""),
            f"inspired by {source_item.name}",
        ]
        
        # Add colors if specified
        if color_palette:
            colors = [color_palette.primary]
            if color_palette.secondary:
                colors.append(color_palette.secondary)
            if color_palette.accent:
                colors.append(color_palette.accent)
            prompt_parts.append(f"colors: {', '.join(colors)}")
        elif source_item.colors:
            prompt_parts.append(f"colors: {', '.join(source_item.colors[:2])}")
        
        # Add tags
        if source_item.tags:
            prompt_parts.append(", ".join(source_item.tags[:3]))
        
        # Add custom additions
        if prompt_additions:
            prompt_parts.append(prompt_additions)
        
        # Quality suffix
        prompt_parts.append("professional fashion photography, high quality")
        
        return ", ".join(filter(None, prompt_parts))
    
    async def download_generated_image(self, image_url: str, design_id: str) -> Optional[str]:
        """Download a generated image and save locally"""
        try:
            save_path = self.settings.generated_dir / f"{design_id}.png"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(save_path, "wb") as f:
                            f.write(content)
                        return str(save_path)
        except Exception as e:
            print(f"Error downloading generated image: {e}")
        
        return None
