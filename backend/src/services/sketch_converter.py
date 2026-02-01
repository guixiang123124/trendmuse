"""
Sketch Converter Service

Converts fashion photos to sketch/technical drawing style.
Uses edge detection for demo, can be upgraded to ControlNet for production.
"""
import uuid
import io
import base64
from datetime import datetime
from typing import Optional
from pathlib import Path
import aiohttp

from src.models.schemas import FashionItem, ConvertedSketch, SketchStyle
from src.core.config import get_settings

# OpenCV import with fallback
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# PIL for image processing
try:
    from PIL import Image, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SketchConverterService:
    """
    Service for converting fashion photos to sketches
    
    Demo mode: Uses edge detection and image filters
    Production: Can integrate ControlNet or similar models
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.demo_mode = self.settings.demo_mode
    
    async def convert_to_sketch(
        self,
        source_item: FashionItem,
        style: SketchStyle = SketchStyle.TECHNICAL,
        detail_level: float = 0.5,
        line_thickness: float = 1.0,
        include_measurements: bool = False
    ) -> ConvertedSketch:
        """
        Convert a fashion item image to sketch style
        
        Args:
            source_item: The original fashion item
            style: Sketch style (technical, pencil, etc.)
            detail_level: Amount of detail (0.1-1.0)
            line_thickness: Line thickness multiplier
            include_measurements: Add measurement annotations
            
        Returns:
            ConvertedSketch with the result
        """
        sketch_id = str(uuid.uuid4())
        
        # Download source image
        image_data = await self._download_image(source_item.image_url)
        
        if image_data and (CV2_AVAILABLE or PIL_AVAILABLE):
            # Process image to create sketch
            sketch_path = await self._create_sketch(
                image_data, sketch_id, style, detail_level, line_thickness
            )
            
            # For demo, we'll serve from local path
            # In production, you'd upload to a CDN
            image_url = f"/api/sketches/{sketch_id}.png"
            local_path = sketch_path
        else:
            # Fallback: return original image URL with note
            image_url = source_item.image_url
            local_path = None
        
        return ConvertedSketch(
            id=sketch_id,
            source_item_id=source_item.id,
            image_url=image_url,
            local_image_path=local_path,
            style=style,
            detail_level=detail_level,
            created_at=datetime.now()
        )
    
    async def _download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"Error downloading image: {e}")
        return None
    
    async def _create_sketch(
        self,
        image_data: bytes,
        sketch_id: str,
        style: SketchStyle,
        detail_level: float,
        line_thickness: float
    ) -> Optional[str]:
        """Create sketch from image data"""
        save_path = self.settings.sketches_dir / f"{sketch_id}.png"
        
        if CV2_AVAILABLE:
            return await self._create_sketch_cv2(
                image_data, save_path, style, detail_level, line_thickness
            )
        elif PIL_AVAILABLE:
            return await self._create_sketch_pil(
                image_data, save_path, style, detail_level
            )
        
        return None
    
    async def _create_sketch_cv2(
        self,
        image_data: bytes,
        save_path: Path,
        style: SketchStyle,
        detail_level: float,
        line_thickness: float
    ) -> str:
        """Create sketch using OpenCV"""
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        if style == SketchStyle.TECHNICAL:
            # Technical drawing style: clean edges
            sketch = self._technical_sketch(gray, detail_level, line_thickness)
        elif style == SketchStyle.PENCIL:
            # Pencil sketch style
            sketch = self._pencil_sketch(gray, detail_level)
        elif style == SketchStyle.INK:
            # Ink drawing style
            sketch = self._ink_sketch(gray, detail_level, line_thickness)
        elif style == SketchStyle.FASHION_ILLUSTRATION:
            # Fashion illustration style
            sketch = self._fashion_illustration(gray, detail_level)
        else:
            # Default: simple edge detection
            sketch = self._simple_edges(gray, detail_level)
        
        # Save sketch
        cv2.imwrite(str(save_path), sketch)
        return str(save_path)
    
    def _technical_sketch(self, gray: np.ndarray, detail: float, thickness: float) -> np.ndarray:
        """Create technical drawing style"""
        # Gaussian blur
        blur_size = max(1, int(5 - detail * 4))
        if blur_size % 2 == 0:
            blur_size += 1
        blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
        
        # Canny edge detection
        low_threshold = int(50 - detail * 30)
        high_threshold = int(150 - detail * 50)
        edges = cv2.Canny(blurred, low_threshold, high_threshold)
        
        # Dilate edges for thickness
        kernel_size = max(1, int(thickness))
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Invert for white background
        sketch = cv2.bitwise_not(dilated)
        
        return sketch
    
    def _pencil_sketch(self, gray: np.ndarray, detail: float) -> np.ndarray:
        """Create pencil sketch style"""
        # Invert
        inverted = cv2.bitwise_not(gray)
        
        # Blur
        blur_val = int(255 - detail * 200)
        if blur_val % 2 == 0:
            blur_val += 1
        blurred = cv2.GaussianBlur(inverted, (blur_val, blur_val), 0)
        
        # Blend (pencil sketch effect)
        sketch = cv2.divide(gray, cv2.bitwise_not(blurred), scale=256.0)
        
        return sketch
    
    def _ink_sketch(self, gray: np.ndarray, detail: float, thickness: float) -> np.ndarray:
        """Create ink drawing style"""
        # Adaptive threshold for ink-like effect
        block_size = int(11 + (1 - detail) * 20)
        if block_size % 2 == 0:
            block_size += 1
        
        sketch = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, block_size, int(2 + detail * 5)
        )
        
        # Optional: dilate for thicker lines
        if thickness > 1:
            kernel_size = int(thickness)
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            edges = cv2.bitwise_not(sketch)
            edges = cv2.dilate(edges, kernel, iterations=1)
            sketch = cv2.bitwise_not(edges)
        
        return sketch
    
    def _fashion_illustration(self, gray: np.ndarray, detail: float) -> np.ndarray:
        """Create fashion illustration style"""
        # Combine pencil and edge effects
        pencil = self._pencil_sketch(gray, detail)
        
        # Add subtle edges
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.bitwise_not(edges)
        
        # Blend
        sketch = cv2.addWeighted(pencil, 0.7, edges, 0.3, 0)
        
        return sketch
    
    def _simple_edges(self, gray: np.ndarray, detail: float) -> np.ndarray:
        """Simple edge detection fallback"""
        edges = cv2.Canny(gray, int(100 - detail * 50), int(200 - detail * 50))
        return cv2.bitwise_not(edges)
    
    async def _create_sketch_pil(
        self,
        image_data: bytes,
        save_path: Path,
        style: SketchStyle,
        detail_level: float
    ) -> str:
        """Create sketch using PIL (fallback)"""
        # Load image
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to grayscale
        gray = ImageOps.grayscale(img)
        
        if style == SketchStyle.PENCIL:
            # Invert and blur for pencil effect
            inverted = ImageOps.invert(gray)
            blurred = inverted.filter(ImageFilter.GaussianBlur(radius=21))
            # Simple dodge blend approximation
            sketch = Image.blend(gray, ImageOps.invert(blurred), 0.5)
        else:
            # Default: edge detection with contour filter
            sketch = gray.filter(ImageFilter.FIND_EDGES)
            sketch = ImageOps.invert(sketch)
        
        # Save
        sketch.save(str(save_path))
        return str(save_path)
    
    # ============================================================
    # CONTROLNET INTEGRATION (For production)
    # ============================================================
    #
    # async def convert_with_controlnet(
    #     self,
    #     source_item: FashionItem,
    #     style: SketchStyle
    # ) -> ConvertedSketch:
    #     """
    #     Convert using ControlNet for higher quality results
    #     
    #     Uses Replicate's ControlNet model with canny edge preprocessor
    #     """
    #     import replicate
    #     
    #     # Style-specific prompts
    #     style_prompts = {
    #         SketchStyle.TECHNICAL: "technical fashion drawing, clean lines, blueprint style",
    #         SketchStyle.FASHION_ILLUSTRATION: "fashion illustration, elegant sketch, marker drawing",
    #         SketchStyle.PENCIL: "pencil sketch, hand-drawn, artistic",
    #         SketchStyle.INK: "ink drawing, bold lines, fashion sketch",
    #         SketchStyle.WATERCOLOR: "watercolor fashion illustration, soft, artistic",
    #     }
    #     
    #     output = replicate.run(
    #         "jagilley/controlnet-canny:aff48af9c68d162388d230a2ab003f68d2638d88307bdaf1c2f1ac95079c9613",
    #         input={
    #             "image": source_item.image_url,
    #             "prompt": style_prompts.get(style, "fashion sketch"),
    #             "structure": "canny",
    #             "num_outputs": 1,
    #         }
    #     )
    #     
    #     return ConvertedSketch(
    #         id=str(uuid.uuid4()),
    #         source_item_id=source_item.id,
    #         image_url=output[0] if output else source_item.image_url,
    #         style=style,
    #         detail_level=0.5,
    #         created_at=datetime.now()
    #     )
    #
    # ============================================================
