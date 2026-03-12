"""Stage 1 — Etsy listing scraper and image downloader.

Scraping strategy (most-stable to least-stable):
  1. JSON-LD structured data  (<script type="application/ld+json">)
  2. Open Graph meta tags      (<meta property="og:*">)
  3. DOM element heuristics    (fallback, fragile)

Rate-limiting: 1 request per 5 seconds with a randomised User-Agent.
Images are downloaded to settings.intake_images_dir / <intake_id> /.
All functions are synchronous — called from async routes via BackgroundTasks.
"""
import json
import mimetypes
import random
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ScraperError(Exception):
    """Raised when scraping fails in a way the caller should handle."""


# ---------------------------------------------------------------------------
# User-Agent pool
# ---------------------------------------------------------------------------

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


def _headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }


# ---------------------------------------------------------------------------
# Etsy listing scraper
# ---------------------------------------------------------------------------


def scrape_etsy_listing(url: str) -> dict:
    """Fetch an Etsy listing and extract structured data.

    Returns a dict with keys:
      raw_title, raw_description, raw_tags (list[str]),
      raw_price_usd (float | None), raw_review_count (int | None),
      raw_rating (float | None), image_urls (list[str])

    Raises ScraperError if the page cannot be fetched or parsed.
    Rate-limits to ~1 req/5s (adds a randomised 4–6s sleep before fetching).
    """
    time.sleep(random.uniform(4.0, 6.0))

    try:
        resp = httpx.get(url, headers=_headers(), follow_redirects=True, timeout=20.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ScraperError(f"HTTP error fetching {url}: {exc}") from exc

    soup = BeautifulSoup(resp.text, "html.parser")
    result: dict = {
        "raw_title": None,
        "raw_description": None,
        "raw_tags": [],
        "raw_price_usd": None,
        "raw_review_count": None,
        "raw_rating": None,
        "image_urls": [],
    }

    # --- Pass 1: JSON-LD structured data -----------------------------------
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = next((d for d in data if d.get("@type") == "Product"), {})
            if data.get("@type") == "Product":
                result["raw_title"] = result["raw_title"] or data.get("name")
                result["raw_description"] = result["raw_description"] or (
                    data.get("description", "")[:1500] or None
                )
                # Images
                imgs = data.get("image", [])
                if isinstance(imgs, str):
                    imgs = [imgs]
                result["image_urls"] = result["image_urls"] or [
                    i for i in imgs if isinstance(i, str)
                ]
                # Price
                offers = data.get("offers", {})
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                price_str = offers.get("price") if isinstance(offers, dict) else None
                if price_str and result["raw_price_usd"] is None:
                    try:
                        result["raw_price_usd"] = float(str(price_str).replace(",", ""))
                    except ValueError:
                        pass
                # Rating / reviews
                agg = data.get("aggregateRating", {})
                if agg and result["raw_rating"] is None:
                    try:
                        result["raw_rating"] = float(agg.get("ratingValue", 0))
                    except (ValueError, TypeError):
                        pass
                    try:
                        result["raw_review_count"] = int(agg.get("reviewCount", 0))
                    except (ValueError, TypeError):
                        pass
        except (json.JSONDecodeError, AttributeError):
            continue

    # --- Pass 2: Open Graph meta tags --------------------------------------
    if not result["raw_title"]:
        og_title = soup.find("meta", property="og:title")
        if og_title:
            result["raw_title"] = og_title.get("content")

    if not result["raw_description"]:
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            result["raw_description"] = (og_desc.get("content") or "")[:1500] or None

    if not result["image_urls"]:
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            result["image_urls"] = [og_img["content"]]

    # --- Pass 3: Etsy-specific DOM heuristics ------------------------------
    # Tags: Etsy renders them in <a> links with URLs containing /search?q=
    if not result["raw_tags"]:
        tag_links = soup.find_all("a", href=re.compile(r"/search\?q="))
        tags = [a.get_text(strip=True) for a in tag_links if a.get_text(strip=True)]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_tags = []
        for t in tags:
            if t not in seen and len(t) > 1:
                seen.add(t)
                unique_tags.append(t)
        result["raw_tags"] = unique_tags[:13]

    # Additional images from data-src attributes on img elements
    if len(result["image_urls"]) < 8:
        for img in soup.find_all("img", {"data-src": True}):
            src = img.get("data-src", "")
            if src.startswith("http") and src not in result["image_urls"]:
                result["image_urls"].append(src)
                if len(result["image_urls"]) >= 8:
                    break

    if not result["raw_title"]:
        raise ScraperError(f"Could not extract title from {url} — page structure may have changed")

    return result


# ---------------------------------------------------------------------------
# Image downloader
# ---------------------------------------------------------------------------


def download_images(
    image_urls: list[str],
    intake_id: str,
    max_images: int = 8,
) -> list[dict]:
    """Download listing images to local storage.

    Saves to: settings.intake_images_dir / intake_id / {index}.{ext}
    Returns list of dicts: {source_url, local_path, file_size_bytes}
    Skips individual images that fail — best-effort.
    """
    dest_dir = Path(settings.intake_images_dir) / intake_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, url in enumerate(image_urls[:max_images]):
        try:
            resp = httpx.get(url, headers=_headers(), follow_redirects=True, timeout=15.0)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            # Normalise .jpe -> .jpg
            if ext in (".jpe", ".jpeg"):
                ext = ".jpg"

            local_path = dest_dir / f"{i}{ext}"
            local_path.write_bytes(resp.content)

            results.append(
                {
                    "source_url": url,
                    "local_path": str(local_path),
                    "file_size_bytes": len(resp.content),
                }
            )
        except Exception:
            # Skip individual download failures — scraping is best-effort
            continue

    return results


# ---------------------------------------------------------------------------
# eRank paste parser
# ---------------------------------------------------------------------------


def parse_erank_paste(paste_text: str) -> dict:
    """Parse a copy-pasted eRank row (tab-separated or comma-separated).

    Returns dict with available keys from:
      source_keyword, raw_price_usd, raw_review_count, raw_title
    Missing fields are omitted from the return dict.
    """
    text = paste_text.strip()
    if not text:
        return {}

    # Detect separator
    sep = "\t" if "\t" in text else ","
    parts = [p.strip().strip('"') for p in text.split(sep)]

    result: dict = {}

    # eRank columns vary by export version; try common patterns
    # Typical order: keyword, search_volume, competition, avg_price, top_seller, ...
    if len(parts) >= 1:
        result["source_keyword"] = parts[0]
    if len(parts) >= 4:
        price_str = re.sub(r"[^\d.]", "", parts[3])
        if price_str:
            try:
                result["raw_price_usd"] = float(price_str)
            except ValueError:
                pass
    if len(parts) >= 5:
        result["raw_title"] = parts[4]

    return result
