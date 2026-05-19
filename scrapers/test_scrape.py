#!/usr/bin/env python
"""Fast test: DB + small IGA scrape (departments + first 10 products)."""
import sys
import os

# Ensure .env is loaded before anything else
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add scrapers package to path
sys.path.insert(0, os.path.dirname(__file__))

from scrapers.db import query, execute

print("=" * 50)
print("TEST 1: DB Connectivity")
print("=" * 50)
rows = query("SELECT id, name, platform, store_id FROM stores")
assert len(rows) == 2, f"Expected 2 stores, got {len(rows)}"
for r in rows:
    print(f"  {r['id']} | {r['name']} | {r['platform']} | {r['store_id']}")
print("PASS\n")

print("=" * 50)
print("TEST 2: IGA Departments (Freshop API)")
print("=" * 50)
from scrapers.iga import scrape_departments

dept_count = scrape_departments()
assert dept_count > 0, "No departments scraped!"
print(f"PASS — {dept_count} departments\n")

print("=" * 50)
print("TEST 3: IGA Products — first 10 only")
print("=" * 50)
from scrapers.iga import fetch

data = fetch("/products", {"store_id": "7432", "limit": 10, "offset": 0})
items = data if isinstance(data, list) else data.get("items", data.get("products", []))
print(f"  API returned {len(items)} products")

if items:
    # Insert them via the _insert_product function
    from scrapers.iga import _insert_product
    for p in items[:10]:
        _insert_product(p)
    print(f"  Inserted {min(10, len(items))} products into Turso")

    # Verify
    count = query("SELECT COUNT(*) as c FROM products WHERE store_id = 'iga-vashon'")[0]["c"]
    print(f"  Verified: {count} IGA products in DB")

assert count > 0, "No IGA products in DB!"
print("PASS\n")

print("=" * 50)
print("TEST 4: Verify price_history")
print("=" * 50)
ph = query("SELECT COUNT(*) as c FROM price_history WHERE store_id = 'iga-vashon'")[0]["c"]
print(f"  {ph} price history records for IGA")
assert ph > 0, "No price history!"
print("PASS\n")

print("=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)
