"""Lamoda size availability fetcher.

Fetches the product page from lamoda.ru, extracts the embedded __NEXT_DATA__
JSON, and maps each SKU entry to {label, available}.
"""
from __future__ import annotations

import asyncio
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
_JSON_LD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

# Gender/section detection signals — same as in the parser
_CAT_URL_SIGNALS: list[tuple[list[str], str]] = [
    (["muzhchinam", "muzhsk", "default-men", "/men/", "male", "dlya-muzhchin"], "men"),
    (["detyam", "detsk", "kid", "child", "boy", "girl", "dlya-detej"], "kids"),
    (["sport", "active", "training", "fitnes"], "sport"),
    (["zhenshchinam", "zhensk", "default-women", "/women/", "female", "dlya-zhenshchin"], "women"),
]
_CAT_NAME_SIGNALS: list[tuple[list[str], str]] = [
    (["мужчинам", "мужской", "мужская", "мужское", "мужские"], "men"),
    (["детям", "мальчикам", "девочкам", "детский", "детская"], "kids"),
    (["спорт", "фитнес", "тренировки"], "sport"),
    (["женщинам", "женский", "женская", "женское", "женские"], "women"),
]


def _cat_from_crumb(url: str, name: str) -> str:
    url_l = url.lower()
    name_l = name.lower()
    for signals, cat in _CAT_URL_SIGNALS:
        if any(s in url_l for s in signals):
            return cat
    for signals, cat in _CAT_NAME_SIGNALS:
        if any(s in name_l for s in signals):
            return cat
    return ""


def _category_from_json_ld(html: str) -> str:
    """Parse JSON-LD BreadcrumbList from page HTML for gender signals."""
    for m in _JSON_LD_RE.finditer(html):
        try:
            ld = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(ld, dict) or ld.get("@type") != "BreadcrumbList":
            continue
        for item in ld.get("itemListElement", []):
            if not isinstance(item, dict):
                continue
            item_obj = item.get("item") or {}
            url = str(item_obj.get("@id", "") or item_obj.get("url", "") or "")
            name = str(item.get("name", "") or "")
            cat = _cat_from_crumb(url, name)
            if cat:
                return cat
    return ""


def _category_from_next_data(data: Any, depth: int = 0) -> str:
    """Recursively search __NEXT_DATA__ for a breadcrumb list with gender signals."""
    if depth > 15:
        return ""
    if isinstance(data, dict):
        for key in ("breadcrumbs", "breadcrumb", "breadcrumbList", "crumbs"):
            crumbs = data.get(key)
            if isinstance(crumbs, list):
                for crumb in crumbs:
                    if not isinstance(crumb, dict):
                        continue
                    url = str(crumb.get("url") or crumb.get("href") or crumb.get("link") or "")
                    name = str(crumb.get("name") or crumb.get("title") or crumb.get("label") or "")
                    cat = _cat_from_crumb(url, name)
                    if cat:
                        return cat
        for v in data.values():
            result = _category_from_next_data(v, depth + 1)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _category_from_next_data(item, depth + 1)
            if result:
                return result
    return ""


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


async def fetch_lamoda_category(sku: str, client: httpx.AsyncClient) -> str | None:
    """Fetch Lamoda product page and return its gender category (men/women/kids/sport).

    Tries JSON-LD BreadcrumbList first (most reliable), then __NEXT_DATA__.
    Returns None if the page can't be fetched or no gender signal found.
    """
    url = f"https://www.lamoda.ru/p/{sku}/"
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=15.0, follow_redirects=True)
        if resp.status_code != 200:
            return None
        html = resp.text
        cat = _category_from_json_ld(html)
        if cat:
            return cat
        m = _NEXT_DATA_RE.search(html)
        if m:
            data = json.loads(m.group(1))
            cat = _category_from_next_data(data)
            if cat:
                return cat
        return None
    except (httpx.TimeoutException, httpx.RequestError, json.JSONDecodeError, ValueError):
        return None


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


# ---------------------------------------------------------------------------
# Standalone sync jobs (used by both HTTP endpoints and the scheduler)
# ---------------------------------------------------------------------------

_sync_lock = asyncio.Lock()
_reclassify_lock = asyncio.Lock()


async def run_full_sync() -> dict:
    """Fetch current size availability for all discounted products and persist.

    Uses an asyncio lock so concurrent calls (scheduler + manual trigger) are
    safe — the second caller gets an immediate no-op response.
    """
    if _sync_lock.locked():
        return {"updated": 0, "skipped": 0, "errors": 0, "total": 0, "already_running": True}

    async with _sync_lock:
        from app.database import AsyncSessionLocal
        from app.models.product import Product
        from app.telegram import send_telegram
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Product)
                .where(Product.discount_percent > 0)
                .where(Product.sku.isnot(None))
                .where(Product.sku != "")
                .where(Product.in_stock.is_(True))
                .order_by(Product.created_at.desc())
            )
            products = result.scalars().all()

            if not products:
                return {"updated": 0, "skipped": 0, "errors": 0, "total": 0}

            updated = skipped = errors = 0
            error_skus: list[str] = []

            async with httpx.AsyncClient() as client:
                for product in products:
                    try:
                        availability = await fetch_lamoda_availability(product.sku, client)
                        if availability is None:
                            skipped += 1
                        else:
                            product.sizes = apply_availability(product.sizes, availability)
                            updated += 1
                    except Exception as exc:
                        errors += 1
                        error_skus.append(f"{product.sku}: {exc}")
                    await asyncio.sleep(0.8)

            await db.commit()

        await send_telegram(
            f"🔄 *Dommoda — синк размеров завершён*\n\n"
            f"✅ Обновлено: {updated}\n"
            f"⏭ Пропущено: {skipped}\n"
            f"❌ Ошибок: {errors}\n"
            f"📦 Всего товаров: {len(products)}"
        )

        return {
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(products),
            "error_skus": error_skus[:10],
        }


async def run_reclassify() -> dict:
    """Re-fetch Lamoda pages for all products with SKU and correct their category.

    Uses BreadcrumbList JSON-LD from each product page — brand-agnostic,
    same signal logic as the parser. Safe to re-run (idempotent).
    """
    if _reclassify_lock.locked():
        return {"updated": 0, "skipped": 0, "errors": 0, "total": 0, "already_running": True}

    async with _reclassify_lock:
        from app.database import AsyncSessionLocal
        from app.models.product import Product
        from app.telegram import send_telegram
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Product)
                .where(Product.sku.isnot(None))
                .where(Product.sku != "")
                .where(Product.in_stock.is_(True))
                .order_by(Product.created_at.desc())
            )
            products = result.scalars().all()

            if not products:
                return {"updated": 0, "skipped": 0, "errors": 0, "total": 0}

            updated = skipped = errors = 0
            error_skus: list[str] = []

            async with httpx.AsyncClient() as client:
                for product in products:
                    try:
                        cat = await fetch_lamoda_category(product.sku, client)
                        if cat is None:
                            skipped += 1
                        elif cat != product.category:
                            product.category = cat
                            updated += 1
                        else:
                            skipped += 1
                    except Exception as exc:
                        errors += 1
                        error_skus.append(f"{product.sku}: {exc}")
                    await asyncio.sleep(0.8)

            await db.commit()

        await send_telegram(
            f"🔁 *Dommoda — реклассификация категорий завершена*\n\n"
            f"✅ Обновлено: {updated}\n"
            f"⏭ Без изменений: {skipped}\n"
            f"❌ Ошибок: {errors}\n"
            f"📦 Всего товаров: {len(products)}"
        )

        return {
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(products),
            "error_skus": error_skus[:10],
        }
