"""
Design Generation Service — Trend → AI Design

Two modes:
  A) Nano Banana (GrsAI) — fast, cheap (1 credit)
  B) Seedream (Volcengine) — high quality (3 credits)
"""
import asyncio
import json
import os
from typing import List, Optional, Dict, Any

import aiohttp

# ── Config ──
GRSAI_API_KEY = os.getenv("GRSAI_API_KEY", "")
GRSAI_API_BASE = os.getenv("GRSAI_API_BASE", "https://api.grsai.com")

VOLC_API_KEY = os.getenv("VOLC_API_KEY", "5e66ff04-4f9c-4fb5-87fe-40e8263e9099")
VOLC_BASE_URL = os.getenv("VOLC_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

SEEDREAM_MODELS = {
    "seedream-4.5": "doubao-seedream-4-5-251128",
    "seedream-5.0-lite": "doubao-seedream-5-0-lite-250210",
}

CREDIT_COST = {
    "nano-banana": 1,
    "seedream-4.5": 3,
    "seedream-5.0-lite": 3,
}

STYLE_PROMPTS = {
    "variation": "Create a design variation that keeps the same overall silhouette and category but changes colors, patterns, and small details.",
    "inspired": "Create a new fashion design inspired by the aesthetic, mood, and trend of this product. Reimagine it with a fresh perspective.",
    "remix": "Remix this design boldly — combine elements with a different style, unexpected colors, or creative pattern mashups.",
}


def build_prompt(title: str, description: str, category: str, style: str) -> str:
    """Build an image generation prompt from product info."""
    style_hint = STYLE_PROMPTS.get(style, STYLE_PROMPTS["variation"])
    parts = [
        f"Fashion product design: {title}.",
        f"Category: {category}." if category else "",
        f"Description: {description}." if description else "",
        style_hint,
        "Professional product photography, white background, e-commerce ready, high quality.",
    ]
    return " ".join(p for p in parts if p)


# ── Nano Banana (GrsAI) ──

async def _generate_nano_banana(
    prompt: str,
    reference_url: Optional[str] = None,
    timeout: int = 120,
) -> Optional[str]:
    """Generate one image via GrsAI Nano Banana SSE stream. Returns image URL."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRSAI_API_KEY}",
    }
    payload: Dict[str, Any] = {
        "model": "nano-banana-fast",
        "prompt": prompt,
        "aspectRatio": "1:1",
    }
    if reference_url:
        payload["urls"] = [reference_url]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GRSAI_API_BASE}/v1/draw/nano-banana",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    print(f"GrsAI error {resp.status}: {await resp.text()}")
                    return None
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    status = data.get("status", "").lower()
                    if status == "succeeded":
                        results = data.get("results", [])
                        if results and results[0].get("url"):
                            return results[0]["url"]
                    elif status == "failed":
                        print(f"GrsAI failed: {data.get('failure_reason')}")
                        return None
    except Exception as e:
        print(f"GrsAI exception: {e}")
    return None


# ── Seedream (Volcengine) ──

async def _generate_seedream(
    prompt: str,
    model: str = "seedream-4.5",
    reference_url: Optional[str] = None,
    timeout: int = 120,
) -> Optional[str]:
    """Generate one image via Volcengine Seedream REST API. Returns image URL."""
    internal_model = SEEDREAM_MODELS.get(model)
    if not internal_model:
        raise ValueError(f"Unknown seedream model: {model}")

    headers = {
        "Authorization": f"Bearer {VOLC_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": internal_model,
        "prompt": prompt,
        "response_format": "url",
        "size": "1920x1920",
        "watermark": False,
    }
    if reference_url:
        payload["image"] = reference_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{VOLC_BASE_URL}/images/generations",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    print(f"Seedream error {resp.status}: {await resp.text()}")
                    return None
                result = await resp.json()
                # Volcengine returns {"data": [{"url": "..."}]}
                data_list = result.get("data", [])
                if data_list and data_list[0].get("url"):
                    return data_list[0]["url"]
    except Exception as e:
        print(f"Seedream exception: {e}")
    return None


# ── Public API ──

async def generate_designs(
    title: str,
    description: str,
    image_url: Optional[str],
    category: str,
    style: str = "variation",
    model: str = "nano-banana",
    count: int = 1,
) -> List[Dict[str, str]]:
    """
    Generate design images.

    Returns list of {"url": ..., "prompt_used": ...}
    """
    prompt = build_prompt(title, description, category, style)
    results: List[Dict[str, str]] = []

    for _ in range(count):
        if model == "nano-banana":
            url = await _generate_nano_banana(prompt, reference_url=image_url)
        elif model in SEEDREAM_MODELS:
            url = await _generate_seedream(prompt, model=model, reference_url=image_url)
        else:
            raise ValueError(f"Unknown model: {model}")

        if url:
            results.append({"url": url, "prompt_used": prompt})

    return results


def get_credit_cost(model: str, count: int) -> int:
    """Return total credit cost for a generation request."""
    per_image = CREDIT_COST.get(model, 1)
    return per_image * count
