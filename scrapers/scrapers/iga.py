"""IGA Vashon Market scraper — Freshop API."""
import time
import httpx, time
from typing import Optional
from scrapers.db import execute, query

BASE_URL = "https://api.freshop.ncrcloud.com"
APP_KEY = "vashon_fresh_market"
STORE_ID = "7432"

def fetch(path: str, params: Optional[dict] = None) -> dict:
    """Call Freshop API with app_key."""
    all_params = {"app_key": APP_KEY}
    if params:
        all_params.update(params)
    url = f"{BASE_URL}{path}"
    response = httpx.get(url, params=all_params, timeout=30)
    response.raise_for_status()
    return response.json()

def scrape_departments():
    """Fetch all IGA departments and insert into DB."""
    data = fetch(f"/departments", {"store_id": STORE_ID})
    departments = data if isinstance(data, list) else data.get("items", data.get("departments", []))

    inserted = 0
    for dept in departments:
        dept_id = str(dept.get("id", dept.get("department_id")))
        name = dept.get("name", dept.get("department_name", ""))
        parent_id = str(dept.get("parent_id")) if dept.get("parent_id") else None

        execute(
            """INSERT OR REPLACE INTO departments (id, store_id, name, parent_id)
               VALUES (?, ?, ?, ?)""",
            [dept_id, "iga-vashon", name, parent_id]
        )
        inserted += 1

    print(f"Inserted/updated {inserted} departments for IGA")
    return inserted

def scrape_products(batch_size: int = 100, delay: float = 1.0):
    """Paginate through all IGA products and insert into DB."""
    offset = 0
    total = 0

    while True:
        data = fetch(
            "/products",
            {"store_id": STORE_ID, "limit": batch_size, "offset": offset, "sort": "name"}
        )
        items = data if isinstance(data, list) else data.get("items", data.get("products", []))

        if not items:
            break

        for product in items:
            _insert_product(product)
            total += 1

        offset += batch_size
        print(f"Scraped {total} products (offset {offset})...")
        time.sleep(delay)

    execute(
        "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = 'iga-vashon'",
        [total]
    )
    print(f"Done. Total: {total} IGA products")
    return total

def _insert_product(product: dict):
    """Insert or update a single product."""
    pid = str(product.get("id"))
    execute(
        """INSERT OR REPLACE INTO products (
            id, store_id, name, price, unit_price, price_display,
            upc, barcode, barcode_type, size, brand, manufacturer,
            department_id, category, image_url, product_url,
            is_weight_required, quantity_label, last_updated_at, is_iga
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            pid,
            "iga-vashon",
            product.get("name", ""),
            product.get("unit_price") or product.get("price"),
            product.get("unit_price"),
            product.get("price") if isinstance(product.get("price"), str) else None,
            str(product.get("upc")) if product.get("upc") else None,
            product.get("barcode") or product.get("barcode_upc_a"),
            product.get("barcode_type", "UPC-A"),
            product.get("size"),
            product.get("brand"),
            product.get("manufacturer"),
            str(product.get("department_ids", [None])[0]) if product.get("department_ids") else None,
            product.get("category"),
            _build_image_url(product),
            product.get("canonical_url"),
            1 if product.get("is_weight_required") else 0,
            product.get("quantity_label"),
            product.get("last_updated_at", None),
            1,
        ]
    )

    price = product.get("unit_price") or product.get("price")
    if price:
        execute(
            "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
            [pid, "iga-vashon", float(price)]
        )

def _build_image_url(product: dict) -> Optional[str]:
    images = product.get("images", [])
    if images and isinstance(images, list) and len(images) > 0:
        identifier = images[0].get("identifier", "")
        if identifier:
            return f"https://images.freshop.ncrcloud.com/{identifier}_medium.jpg"
    return None

if __name__ == "__main__":
    scrape_departments()
    scrape_products()
