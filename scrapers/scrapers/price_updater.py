"""Match Mercato prices to Thriftway Freshop products and update DB."""
from thefuzz import fuzz
from scrapers.db import query, execute

def update_thriftway_prices(mercato_results: list[dict]):
    updated = 0
    for result in mercato_results:
        top = result["top_result"]
        mercato_name = top["name"]
        mercato_price = _parse_price(top["price"])
        if mercato_price is None:
            continue
        
        candidates = query(
            """SELECT id, name, price FROM products
               WHERE store_id = 'thriftway-vashon'
               AND name LIKE ?
               LIMIT 20""",
            [f"%{result['query'].split()[0]}%"]
        )
        
        best_match = None
        best_score = 0
        for c in candidates:
            score = fuzz.token_sort_ratio(mercato_name.lower(), c["name"].lower())
            if score > best_score:
                best_score = score
                best_match = c
        
        if best_match and best_score > 60:
            execute(
                """UPDATE products SET
                   price = ?, price_display = ?, last_updated_at = datetime('now')
                   WHERE id = ?""",
                [mercato_price, top["price"], best_match["id"]]
            )
            execute(
                "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
                [best_match["id"], "thriftway-vashon", mercato_price]
            )
            updated += 1
            print(f"  Updated '{best_match['name'][:50]}' -> ${mercato_price} (score: {best_score})")
        else:
            print(f"  No match for '{mercato_name[:50]}' (best: {best_score})")
    
    print(f"\nUpdated {updated} Thriftway prices from Mercato")
    return updated

def _parse_price(price_str: str) -> float | None:
    import re
    match = re.search(r'[\d.]+', str(price_str))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None
