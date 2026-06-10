"""Lamoda size availability fetcher.

Fetches the product page from lamoda.ru, extracts the embedded __NEXT_DATA__
JSON, and maps each SKU entry to {label, available}.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


def _find_skus(data: Any, depth: int = 0) -> list[dict] | None:
    """Recursively locate the 'skus' array in Lamoda's __NEXT_DATA__ JSON."""
    if depth > 12:
        return None
    if isinstance(data, dict):
        if "skus" in data and isinstance(data["skus"], list) and data["skus"]:
            candidate = data["skus"]
            # Validate: each entry should be a dict with a 'size' key
            if isinstance(candidate[0], dict) and (
                "size" in candidate[0] or "qty" in candidate[0]
            ):
                return candidate
        for v in data.values():
            result = _find_skus(v, depth + 1)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_skus(item, depth + 1)
            if result is not None:
                return result
    return None


def _skus_to_availability(skus: list[dict]) -> dict[str, bool]:
    """Convert Lamoda skus list → {size_label: is_available}."""
    result: dict[str, bool] = {}
    for entry in skus:
        if not isinstance(entry, dict):
            continue
        size_obj = entry.get("size")
        if isinstance(size_obj, dict):
            label = (
                size_obj.get("sizeRu")
                or size_obj.get("size_ru")
                or size_obj.get("size")
                or size_obj.get("label")
            )
        elif isinstance(size_obj, str):
            label = size_obj
        else:
            continue
        if not label:
            continue
        label = str(label).strip()
        qty = entry.get("qty", entry.get("quantity", 0))
        try:
            available = int(qty) > 0
        except (TypeError, ValueError):
            available = bool(qty)
        result[label] = available
    return result


async def fetch_lamoda_availability(sku: str, client: httpx.AsyncClient) -> dict[str, bool] | None:
    """
    Fetch Lamoda product page and return {size_label: is_available}.
    Returns None if the page can't be fetched or parsed.
    """
    url = f"https://www.lamoda.ru/p/{sku}/"
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=15.0, follow_redirects=True)
        if resp.status_code != 200:
            return None
        match = _NEXT_DATA_RE.search(resp.text)
        if not match:
            return None
        data = json.loads(match.group(1))
        skus = _find_skus(data)
        if not skus:
            return None
        return _skus_to_availability(skus)
    except (httpx.TimeoutException, httpx.RequestError, json.JSONDecodeError, ValueError):
        return None


def apply_availability(
    existing_sizes: list[dict],
    availability: dict[str, bool],
) -> list[dict]:
    """
    Merge Lamoda availability into our sizes list.
    Sizes not found on Lamoda are marked unavailable.
    """
    updated = []
    for s in existing_sizes:
        label = s.get("label", "")
        if label in availability:
            updated.append({"label": label, "available": availability[label]})
        else:
            # Size not listed on Lamoda — treat as out of stock
            updated.append({"label": label, "available": False})
    return updated
