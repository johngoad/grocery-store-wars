"""Backfill IGA price_display from price + size fields."""
import os
from scrapers.db import query, execute

def backfill():
    products = query(
        "SELECT id, price, size, price_display FROM products WHERE is_iga=1"
    )
    
    updated = 0
    for p in products:
        if p["price_display"]:
            continue  # already populated
        
        price = p["price"]
        size = p.get("size", "") or ""
        
        if price is None:
            continue
        
        # Format price
        price_str = f"${price:.2f}"
        
        # Add unit suffix if size exists
        size_lower = size.lower().strip()
        if size_lower in ("lb", "lbs"):
            display = f"{price_str} / lb"
        elif size_lower == "ea":
            display = f"{price_str} each"
        elif "oz" in size_lower:
            display = f"{price_str} ({size})"
        elif "ct" in size_lower:
            display = f"{price_str} ({size})"
        elif size_lower in ("qt", "pint", "gal", "fl oz"):
            display = f"{price_str} ({size})"
        elif size:
            display = f"{price_str} ({size})"
        else:
            display = price_str
        
        execute(
            "UPDATE products SET price_display = ? WHERE id = ?",
            [display, p["id"]]
        )
        updated += 1
    
    print(f"Backfilled {updated} IGA price_display fields")

if __name__ == "__main__":
    backfill()
