#!/usr/bin/env python
"""Full IGA Vashon Market scrape — all departments + all products."""
import sys, os, time
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.path.insert(0, os.path.dirname(__file__))

from scrapers.iga import scrape_departments, scrape_products
from scrapers.db import query

start = time.time()

print("Step 1/2: Scraping departments...")
dept_count = scrape_departments()
print(f"  {dept_count} departments updated\n")

print("Step 2/2: Scraping all products (paginating, ~12K products)...")
product_count = scrape_products(batch_size=100, delay=1.0)

elapsed = time.time() - start

# Final verification
store = query("SELECT id, last_scraped_at, product_count FROM stores WHERE id = 'iga-vashon'")
price_count = query("SELECT COUNT(*) as c FROM price_history WHERE store_id = 'iga-vashon'")
dept_verify = query("SELECT COUNT(*) as c FROM departments WHERE store_id = 'iga-vashon'")

print(f"\n=== FULL SCRAPE COMPLETE ({elapsed:.0f}s) ===")
print(f"  Products:   {product_count}")
print(f"  Price pts:  {price_count[0]['c']}")
print(f"  Departments: {dept_verify[0]['c']}")
print(f"  DB updated: {store[0]['last_scraped_at']}")
