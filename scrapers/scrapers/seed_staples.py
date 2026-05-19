"""Seed staple items for KPI dashboard."""
from thefuzz import fuzz
from scrapers.db import query, execute

STAPLES = [
    ("Milk (1 gal)", "milk whole gallon", "dairy", 1),
    ("Eggs (12 ct)", "eggs large dozen", "dairy", 2),
    ("Ground Beef 80/20", "ground beef 80", "meat", 3),
    ("Chicken Breast", "chicken breast boneless", "meat", 4),
    ("Sourdough Bread", "sourdough bread", "bakery", 5),
    ("Mayonnaise (30oz)", "mayonnaise hellmann", "pantry", 6),
    ("Butter (1 lb)", "butter unsalted", "dairy", 7),
    ("Cheddar Cheese", "cheese cheddar", "dairy", 8),
    ("Bananas", "bananas", "produce", 9),
    ("Coffee (12oz)", "coffee ground", "pantry", 10),
    ("Bacon", "bacon", "meat", 11),
    ("Toilet Paper", "toilet paper", "household", 12),
    ("Laundry Detergent", "laundry detergent", "household", 13),
    ("Olive Oil", "oil olive", "pantry", 14),
    ("Orange Juice", "orange juice", "beverages", 15),
]

def seed():
    for name, search, category, order in STAPLES:
        iga = _find_best(search, is_iga=1)
        tw = _find_best(search, is_iga=0)
        
        execute(
            """INSERT OR REPLACE INTO staple_items
               (name, iga_product_id, thriftway_product_id, category, display_order)
               VALUES (?, ?, ?, ?, ?)""",
            [
                name,
                iga["id"] if iga else None,
                tw["id"] if tw else None,
                category,
                order,
            ]
        )
        iga_price = iga.get("price_display", "N/A") if iga else "N/A"
        tw_price = tw.get("price_display", "N/A") if tw else "N/A"
        print(f"  {name}: IGA {iga_price} | TW {tw_price}")

def _find_best(search: str, is_iga: int) -> dict | None:
    terms = search.split()
    candidates = query(
        f"""SELECT id, name, price_display FROM products
            WHERE is_iga = ? AND (name LIKE ? OR name LIKE ?)
            LIMIT 30""",
        [is_iga, f"%{terms[0]}%", f"%{terms[1]}%" if len(terms) > 1 else f"%{terms[0]}%"]
    )
    if not candidates:
        return None
    
    best = max(candidates, key=lambda c: fuzz.partial_ratio(search, c["name"].lower()))
    return best

if __name__ == "__main__":
    seed()
