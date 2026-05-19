"""Thriftway scraper — Freshop catalog (stale) + Mercato prices (current, limited)."""
import time
import httpx
from scrapers.db import execute

FRESHOP_BASE = "https://api.freshop.ncrcloud.com"
FRESHOP_APP_KEY = "vashon_thriftway"
FRESHOP_STORE_ID = "1813"

def fetch_freshop(path: str, params: dict | None = None) -> dict:
    all_params = {"app_key": FRESHOP_APP_KEY}
    if params:
        all_params.update(params)
    url = f"{FRESHOP_BASE}{path}"
    response = httpx.get(url, params=all_params, timeout=30)
    response.raise_for_status()
    return response.json()

def scrape_thriftway_catalog(batch_size: int = 100, delay: float = 0.5, max_products: int | None = None):
    """Scrape Thriftway product catalog from Freshop (prices are stale — metadata is good)."""
    offset = 0
    total = 0
    
    while True:
        data = fetch_freshop(
            "/products",
            {"store_id": FRESHOP_STORE_ID, "limit": batch_size, "offset": offset}
        )
        items = data if isinstance(data, list) else data.get("items", data.get("products", []))
        
        if not items:
            break
        
        for product in items:
            pid = f"tw-freshop-{product.get('id')}"
            execute(
                """INSERT OR REPLACE INTO products (
                    id, store_id, name, price, unit_price, price_display,
                    upc, barcode, size, brand, department_id, category,
                    image_url, product_url, last_updated_at, is_iga
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    pid,
                    "thriftway-vashon",
                    product.get("name", ""),
                    product.get("unit_price"),
                    product.get("unit_price"),
                    product.get("price") if isinstance(product.get("price"), str) else None,
                    str(product.get("upc")) if product.get("upc") else None,
                    product.get("barcode") or product.get("barcode_upc_a"),
                    product.get("size"),
                    product.get("brand"),
                    str(product.get("department_ids", [None])[0]) if product.get("department_ids") else None,
                    product.get("category"),
                    f"https://images.freshop.ncrcloud.com/{product.get('images', [{}])[0].get('identifier', '')}_medium.jpg" if product.get("images") else None,
                    product.get("canonical_url"),
                    "2020-03-01",
                    0,
                ]
            )
            total += 1
        
        offset += batch_size
        print(f"Thriftway catalog: {total} products (offset {offset})...")
        
        if max_products and total >= max_products:
            break
        
        time.sleep(delay)
    
    execute(
        "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = 'thriftway-vashon'",
        [total]
    )
    print(f"Done. Total: {total} Thriftway catalog products")
    return total

if __name__ == "__main__":
    scrape_thriftway_catalog()
