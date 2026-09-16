#!/usr/bin/env python3
"""
scrape-brand-products.py — Download product images from a brand website.

Attempts to fetch products via Shopify's JSON API first.
Falls back to HTML page scraping if the API is unavailable.

Run from the project root:
  python3 scripts/scrape-brand-products.py --url https://brand.com --out brands/brand-name

Outputs (inside --out directory):
  product-images/   — downloaded product images
  products.json     — product index (name, filename, page_url)
"""

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

VALID_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp"}

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

PRODUCT_PATH_SEGMENTS = {"/products/", "/shop/", "/store/"}


# ---------------------------------------------------------------------------
# HTML parsers
# ---------------------------------------------------------------------------

class OGTagParser(HTMLParser):
    """Extract Open Graph meta tag values from HTML."""

    def __init__(self):
        super().__init__()
        self._data: dict = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        attrs_dict = dict(attrs)
        prop = attrs_dict.get("property") or attrs_dict.get("name") or ""
        content = attrs_dict.get("content", "").strip()
        if prop.startswith("og:") and content and prop not in self._data:
            self._data[prop] = content

    def get(self, property_name: str) -> str:
        return self._data.get(f"og:{property_name}", "")


class ProductLinkParser(HTMLParser):
    """Extract product page links from an HTML page."""

    def __init__(self, domain: str):
        super().__init__()
        self._domain = domain
        self._seen: set = set()
        self.links: list = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href", "")
        if not href or not any(seg in href for seg in PRODUCT_PATH_SEGMENTS):
            return
        url = self._normalise(href)
        if url and url not in self._seen:
            self._seen.add(url)
            self.links.append(url)

    def _normalise(self, href: str) -> str:
        href = href.split("?")[0].split("#")[0]
        if href.startswith("//"):
            return f"https:{href}"
        if href.startswith("/"):
            return f"{self._domain}{href}"
        if href.startswith("http"):
            return href
        return ""


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def to_slug(text: str, max_chars: int = 60) -> str:
    """Convert a product name to a lowercase hyphenated filename slug."""
    chars = []
    last_sep = True
    for ch in text.lower():
        if ch.isalnum():
            chars.append(ch)
            last_sep = False
        elif not last_sep:
            chars.append("-")
            last_sep = True
    slug = "".join(chars).rstrip("-")
    return slug[:max_chars]


def image_extension(url: str) -> str:
    ext = Path(urlparse(url).path).suffix.lower()
    return ext if ext in VALID_IMAGE_TYPES else ".jpg"


def strip_query(url: str) -> str:
    return url.split("?")[0]


def fetch_url(url: str, timeout: int = 15):
    try:
        response = requests.get(url, timeout=timeout, headers=REQUEST_HEADERS)
        return response if response.ok else None
    except Exception:
        return None


def save_image(url: str, destination: Path) -> bool:
    try:
        response = requests.get(url, timeout=30, headers=REQUEST_HEADERS)
        response.raise_for_status()
        destination.write_bytes(response.content)
        return True
    except Exception as err:
        print(f"    Could not download: {err}")
        return False


# ---------------------------------------------------------------------------
# Product fetchers
# ---------------------------------------------------------------------------

def fetch_via_shopify(domain: str, limit: int) -> list:
    """Fetch products using Shopify's products.json endpoint."""
    endpoint = f"{domain}/products.json?sort_by=best-selling&limit={limit}"
    response = fetch_url(endpoint)
    if not response:
        return []
    try:
        payload = response.json()
    except Exception:
        return []

    results = []
    for item in payload.get("products", [])[:limit]:
        images = item.get("images", [])
        if not images:
            continue
        results.append({
            "name":        item["title"],
            "handle":      item["handle"],
            "image_url":   strip_query(images[0]["src"]),
            "page_url": f"{domain}/products/{item['handle']}",
            # Phase 3.0 — capture richer fields for product DNA auto-fill.
            # All optional; downstream skills handle missing values gracefully.
            "description_html": item.get("body_html") or "",
            "product_type":     item.get("product_type") or "",
            "tags":             item.get("tags") or [],
            "vendor":           item.get("vendor") or "",
        })
    return results


def fetch_via_html(domain: str, original_url: str, limit: int) -> list:
    """Fallback scraper — finds product links then reads og: tags from each page."""
    candidate_pages = [
        f"{domain}/collections/all",
        f"{domain}/collections/best-sellers",
        f"{domain}/collections/bestsellers",
        f"{domain}/shop",
        f"{domain}/products",
        original_url,
    ]

    product_links: list = []
    for page in candidate_pages:
        response = fetch_url(page, timeout=10)
        if not response:
            continue
        parser = ProductLinkParser(domain)
        try:
            parser.feed(response.text)
        except Exception:
            continue
        if parser.links:
            product_links = parser.links
            break

    results = []
    for link in product_links[: limit * 2]:
        response = fetch_url(link, timeout=10)
        if not response:
            continue

        og = OGTagParser()
        try:
            og.feed(response.text)
        except Exception:
            continue

        name    = og.get("title") or link.rstrip("/").split("/")[-1]
        img_url = og.get("image")
        if not img_url:
            continue

        if img_url.startswith("//"):
            img_url = f"https:{img_url}"
        elif img_url.startswith("/"):
            img_url = f"{domain}{img_url}"

        results.append({
            "name":        name,
            "handle":      link.rstrip("/").split("/")[-1],
            "image_url":   strip_query(img_url),
            "page_url": link,
        })

        if len(results) >= limit:
            break

    return results


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def download_brand_products(site_url: str, out_dir: Path, max_items: int = 20) -> list:
    """Fetch and download product images into out_dir."""
    site_url = site_url.rstrip("/")
    if not urlparse(site_url).scheme:
        site_url = f"https://{site_url}"

    parsed = urlparse(site_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    image_dir = out_dir / "product-images"
    image_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nFetching products from {domain}...\n")

    products = fetch_via_shopify(domain, max_items)
    if products:
        print(f"  Found {len(products)} products via Shopify API.")
    else:
        print("  Shopify API unavailable — trying page scrape...")
        products = fetch_via_html(domain, site_url, max_items)
        if products:
            print(f"  Found {len(products)} products via page scrape.")
        else:
            print("  Could not find products automatically.")
            print(f"  Add product images manually to {image_dir}/ and create {out_dir}/products.json")
            return []

    print(f"\nDownloading images to {image_dir}/...\n")

    index = []
    used_filenames: set = set()

    for product in products[:max_items]:
        base = to_slug(product["name"])
        ext  = image_extension(product["image_url"])

        candidate = f"{base}{ext}"
        suffix = 2
        while candidate in used_filenames:
            candidate = f"{base}-{suffix}{ext}"
            suffix += 1
        used_filenames.add(candidate)

        file_path = image_dir / candidate

        if file_path.exists():
            print(f"  ✓ {candidate} (already downloaded)")
        else:
            print(f"  {product['name']}...", end=" ", flush=True)
            if not save_image(product["image_url"], file_path):
                continue
            print("✓")

        entry = {
            "name":        product["name"],
            "filename":    candidate,
            "page_url":    product["page_url"],
        }
        # Phase 3.0 — include richer Shopify fields when present.
        # /brand-dna-builder Step 6 reads these to auto-fill product-dna.md.
        # All optional; downstream skills handle missing values gracefully.
        if product.get("description_html"):
            entry["description_html"] = product["description_html"]
        if product.get("product_type"):
            entry["product_type"] = product["product_type"]
        if product.get("tags"):
            entry["tags"] = product["tags"]
        if product.get("vendor"):
            entry["vendor"] = product["vendor"]
        index.append(entry)

    if not index:
        print("\n  No images were saved.")
        return []

    products_json = out_dir / "products.json"
    with open(products_json, "w") as f:
        json.dump({"products": index}, f, indent=2)

    print(f"\n  {len(index)} product image(s) saved to {image_dir}/")
    print(f"  Product index written to {products_json}\n")

    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download product images from a brand website."
    )
    parser.add_argument("--url",   type=str, required=True,  metavar="URL",
                        help="Brand website URL (e.g. https://brand.com)")
    parser.add_argument("--out",   type=str, required=True,  metavar="DIR",
                        help="Output directory (e.g. brands/pynk)")
    parser.add_argument("--limit", type=int, default=20,     metavar="N",
                        help="Maximum number of products to download (default: 20)")
    args = parser.parse_args()
    download_brand_products(args.url, Path(args.out), max_items=args.limit)


if __name__ == "__main__":
    main()
