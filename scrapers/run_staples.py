"""Seed staple items for KPI dashboard — optimized with word-index fuzzy matching."""
from collections import defaultdict
from thefuzz import fuzz, process
from scrapers.db import query, execute

STAPLES = [
    ("Milk (1 gal)", "milk whole gallon", "dairy", 1),
    ("Eggs (12 ct)", "eggs large dozen grade a", "dairy", 2),
    ("Ground Beef 80/20", "ground beef 80 20 chuck", "meat", 3),
    ("Chicken Breast", "chicken breast boneless skinless", "meat", 4),
    ("Sourdough Bread", "sourdough bread loaf", "bakery", 5),
    ("Mayonnaise (30oz)", "mayonnaise hellmann", "pantry", 6),
    ("Butter (1 lb)", "butter unsalted sweet cream", "dairy", 7),
    ("Cheddar Cheese", "cheese cheddar sharp", "dairy", 8),
    ("Bananas", "bananas yellow organic", "produce", 9),
    ("Coffee (12oz)", "coffee ground medium roast", "pantry", 10),
    ("Bacon", "bacon thick cut", "meat", 11),
    ("Toilet Paper", "toilet paper bath tissue", "household", 12),
    ("Laundry Detergent", "laundry detergent liquid", "household", 13),
    ("Olive Oil", "oil olive extra virgin", "pantry", 14),
    ("Orange Juice", "orange juice pulp", "beverages", 15),
    ("Flour (5 lb)", "flour all purpose white", "pantry", 16),
    ("Sugar (4 lb)", "sugar granulated white", "pantry", 17),
    ("Sliced Turkey", "turkey breast sliced deli", "deli", 18),
    ("Pasta (1 lb)", "pasta spaghetti", "pantry", 19),
    ("Tomato Sauce", "tomato sauce marinara", "pantry", 20),
]

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with",
    "lb", "lbs", "oz", "ozs", "ct", "cts", "ea", "pk", "pkg", "fl",
    "organic", "fresh", "natural", "original",
}

def _normalize(s):
    if not s:
        return ""
    return s.lower().strip().replace("'s", "s").replace("  ", " ")

def _get_first_significant_word(name):
    words = name.split()
    for w in words:
        w = w.strip("(),.-")
        if w and w not in STOP_WORDS and len(w) > 1:
            return w
    return words[0] if words else ""

def _build_index(is_iga):
    """Build word-index for a store's products."""
    products = query(
        "SELECT id, name, price_display, price FROM products WHERE is_iga = ?",
        [is_iga]
    )
    index = defaultdict(list)
    for p in products:
        word = _get_first_significant_word(_normalize(p["name"]))
        index[word].append(p)
    return products, index

def seed():
    print("Building indices...")
    iga_products, iga_index = _build_index(1)
    tw_products, tw_index = _build_index(0)
    print(f"  IGA: {len(iga_products)} products, {len(iga_index)} words")
    print(f"  TW: {len(tw_products)} products, {len(tw_index)} words")

    for name, search, category, order in STAPLES:
        print(f"\n{name}:")
        search_terms = [t for t in search.split() if t not in STOP_WORDS]

        # Find best in IGA
        iga = _find_best_indexed(search_terms, iga_index)
        # Find best in Thriftway
        tw = _find_best_indexed(search_terms, tw_index)

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

        iga_price = iga.get("price_display", "N/A") if iga else "NOT FOUND"
        tw_price = tw.get("price_display", "N/A") if tw else "NOT FOUND"
        iga_name = iga["name"][:55] if iga else "-"
        tw_name = tw["name"][:55] if tw else "-"
        print(f"  IGA: {iga_name:55s} {iga_price}")
        print(f"  TW:  {tw_name:55s} {tw_price}")


def _find_best_indexed(search_terms, index):
    """Find best product match using word-indexed fuzzy search."""
    # Try matching against each search term's word group
    candidates = []
    seen_ids = set()
    for term in search_terms:
        for word, prods in index.items():
            if word.startswith(term) or term in word:
                for p in prods:
                    if p["id"] not in seen_ids:
                        candidates.append(p)
                        seen_ids.add(p["id"])

    if not candidates:
        return None

    search_str = " ".join(search_terms)
    cand_names = [_normalize(c["name"]) for c in candidates]

    # Find best match
    result = process.extractOne(
        search_str,
        cand_names,
        scorer=fuzz.token_sort_ratio,
    )

    if result:
        best_name, score = result
        idx = cand_names.index(best_name)
        return candidates[idx]

    return None


if __name__ == "__main__":
    seed()
