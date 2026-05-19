#!/usr/bin/env python
"""Test Turso DB connection from scrapers."""
import scrapers
from scrapers.db import query

rows = query("SELECT id, name, platform, store_id FROM stores")
assert len(rows) == 2, f"Expected 2 stores, got {len(rows)}"
for r in rows:
    print(r)
print("OK — DB connection works")
