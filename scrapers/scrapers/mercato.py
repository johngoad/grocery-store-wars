"""Mercato scraper for Thriftway Vashon — REST API, no Playwright needed.

Hits Mercato's internal API:
  /api/search-meta      → categories (storeId=1279)
  /api/store/products-grouped → products by category, paginated
"""
import time, re, sys, os
import httpx
from scrapers.db import execute, query

MERCATO_BASE = "https://www.mercato.com"
STORE_ID = "thriftway-vashon"
STORE_NAME = "vashon-thriftway"
STORE_NUMERIC_ID = 1279

client = httpx.Client(timeout=60)

# --- Category fetch ---

def fetch_categories() -> list[dict]:
    """Get all product categories with IDs and counts."""
    resp = client.get(
        f"{MERCATO_BASE}/api/search-meta",
        params={"ajax": "true", "storeId": STORE_NUMERIC_ID, "getAllCategories": "true"}
    )
    resp.raise_for_status()
    data = resp.json()
    cats = data.get("categories", [])
    # Filter out "All" (id=None) and sub-100-count categories unless we want them
    return [c for c in cats if c.get("id") is not None and c.get("count", 0) > 0]


# --- Product fetch ---

def fetch_products_all(category_id: int, limit: int, sort: str = "name") -> list[dict]:
    """Fetch ALL products for a category in a single request (no pagination)."""
    resp = client.get(
        f"{MERCATO_BASE}/api/store/products-grouped/{STORE_NAME}",
        params={
            "ajax": "true",
            "productCategoryIds": category_id,
            "limit": limit,
            "offset": 0,
            "loadProducts": "true",
            "sort": sort,
            "sortDir": "asc",
        }
    )
    resp.raise_for_status()
    data = resp.json()
    for cat in data.get("categories", []):
        return cat.get("products", [])
    return []


def fetch_all_products_multi_sort(category_id: int, expected: int, batch_limit: int = 5000) -> list[dict]:
    """Fetch ALL products using multiple sort orders when a single request
    doesn't return everything (API doesn't support offset pagination).
    Different sort orders yield different product subsets with ~98% uniqueness."""
    all_by_id = {}
    sort_passes = [("name", "asc"), ("price", "asc"), ("name", "desc")]

    for sort_field, sort_dir in sort_passes:
        if len(all_by_id) >= expected:
            break
        
        resp = client.get(
            f"{MERCATO_BASE}/api/store/products-grouped/{STORE_NAME}",
            params={
                "ajax": "true",
                "productCategoryIds": category_id,
                "limit": batch_limit,
                "offset": 0,
                "loadProducts": "true",
                "sort": sort_field,
                "sortDir": sort_dir,
            }
        )
        resp.raise_for_status()
        data = resp.json()
        batch = []
        for cat in data.get("categories", []):
            batch = cat.get("products", [])
        
        before = len(all_by_id)
        for p in batch:
            pid = p.get("productId")
            if pid and pid not in all_by_id:
                all_by_id[pid] = p
        new = len(all_by_id) - before
        
        if new == 0:
            break  # No new products from this sort — we've exhausted the category

    return list(all_by_id.values())


# --- Price parsing ---

def parse_price(price_display=None):
    """Extract numeric price from display string like '$2.99 per lb' or '$4.29 each'."""
    if not price_display:
        return None
    nums = re.findall(r'\d+\.?\d*', price_display.replace(',', ''))
    if nums:
        return float(nums[0])
    return None


# --- DB insert ---

def insert_product(product: dict, category_name: str, category_id: int):
    """Insert or update a Mercato product in Turso DB."""
    pid = f"mercato-{product['productId']}"
    name = (product.get("name") or "")[:200]
    price_display = product.get("priceDisplay") or ""
    price = parse_price(price_display)
    unit = product.get("unitOfMeasurement") or ""
    image = product.get("mediumImageUrl") or ""

    execute(
        """INSERT OR REPLACE INTO products (
            id, store_id, name, price, price_display, unit_price,
            size, department_id, category, image_url,
            last_updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        [
            pid, STORE_ID, name,
            price,
            price_display,
            price,
            unit,
            str(category_id),
            category_name,
            image,
        ]
    )

    if price is not None:
        execute(
            "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
            [pid, STORE_ID, price]
        )

    return pid


# --- Main scrape ---

def scrape_all(delay: float = 0.3, batch_limit: int = 5000):
    """Scrape all products across all categories.
    For categories smaller than batch_limit, one request suffices.
    For larger categories, uses multi-sort to work around broken pagination."""
    categories = fetch_categories()
    print(f"Found {len(categories)} categories")
    total_expected = sum(c.get("count", 0) for c in categories)
    print(f"Expected total products: {total_expected:,}")

    total_inserted = 0
    for ci, cat in enumerate(categories):
        cat_id = cat["id"]
        cat_name = cat["name"]
        cat_count = cat.get("count", 0)

        label = f"[{ci+1}/{len(categories)}] {cat_name} ({cat_count} products)"
        print(f"{label} ... ", end="", flush=True)

        if cat_count <= batch_limit:
            # Simple: one request gets everything
            products = fetch_products_all(cat_id, limit=cat_count + 100)
        else:
            # Large category: use multi-sort to collect all products
            products = fetch_all_products_multi_sort(cat_id, cat_count, batch_limit=batch_limit)

        for prod in products:
            insert_product(prod, cat_name, cat_id)

        total_inserted += len(products)
        coverage = f"({len(products)/cat_count*100:.0f}%)" if cat_count else ""
        print(f"got {len(products)} {coverage}")

        if ci < len(categories) - 1:
            time.sleep(delay)

    execute(
        "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = ?",
        [total_inserted, STORE_ID]
    )
    print(f"\n=== TOTAL: {total_inserted} products across {len(categories)} categories ===")
    return total_inserted


if __name__ == "__main__":
    scrape_all()
