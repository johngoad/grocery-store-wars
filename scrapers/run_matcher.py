"""Optimized product matcher — UPC exact + indexed fuzzy name matching."""
import re
from collections import defaultdict
from thefuzz import fuzz, process
from scrapers.db import query, batch_execute

UPC_MATCH_CONFIDENCE = 1.0
FUZZY_NAME_THRESHOLD = 85
SIZE_BONUS = 0.05
BRAND_BONUS = 0.05
# How many top candidates to fuzzy-match per product
TOP_N_CANDIDATES = 50

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with",
    "lb", "lbs", "oz", "ozs", "ct", "cts", "ea", "pk", "pkg", "fl",
    "organic", "fresh", "natural", "original",
}

def _normalize(s):
    if not s:
        return ""
    return s.lower().strip().replace("'s", "s").replace("  ", " ")

def _get_first_significant_word(name: str) -> str:
    """Get first word that isn't a stop word or common prefix."""
    words = name.split()
    for w in words:
        w = w.strip("(),.-")
        if w and w not in STOP_WORDS and len(w) > 1:
            return w
    return words[0] if words else ""

def _get_upcs(product: dict) -> set:
    upcs = set()
    for field in ["upc", "barcode"]:
        val = product.get(field)
        if val:
            code = str(val).strip().lstrip("0")
            upcs.add(code)
            upcs.add(code.zfill(12))
    return upcs

def match_all(min_confidence: float = 0.70):
    print("Loading products...")
    iga_products = query(
        "SELECT id, name, upc, barcode, size, brand FROM products WHERE is_iga=1"
    )
    tw_products = query(
        "SELECT id, name, upc, barcode, size, brand FROM products WHERE is_iga=0"
    )
    print(f"  IGA: {len(iga_products)} | Thriftway: {len(tw_products)}")

    # Build UPC index for O(1) lookup
    tw_by_upc = {}
    for p in tw_products:
        for code in _get_upcs(p):
            if code and len(code) >= 10:  # real UPCs are 10-13 digits
                tw_by_upc[code] = p
    print(f"  UPC index: {len(tw_by_upc)} codes from Thriftway")

    # Build inverted index by first significant word for fast candidate selection
    tw_by_word = defaultdict(list)
    for p in tw_products:
        word = _get_first_significant_word(_normalize(p["name"]))
        tw_by_word[word].append(p)
    print(f"  Word index: {len(tw_by_word)} unique first-words")

    # Build candidate index: for each IGA product, collect candidates
    # (same first-word group, plus UPC matches)
    matched = 0
    upc_matches = 0
    fuzzy_matches = 0
    statements = []

    for i, iga in enumerate(iga_products):
        if (i + 1) % 500 == 0:
            print(f"  Processing {i+1}/{len(iga_products)}... ({matched} matched so far)")

        best_id = None
        best_confidence = 0.0
        match_type = "fuzzy_name"

        # Strategy 1: Exact UPC match
        for upc in _get_upcs(iga):
            if upc in tw_by_upc and len(upc) >= 10:
                best_id = tw_by_upc[upc]["id"]
                best_confidence = UPC_MATCH_CONFIDENCE
                match_type = "upc_exact"
                break

        # Strategy 2: Fuzzy name matching with indexed candidates
        if best_confidence < UPC_MATCH_CONFIDENCE:
            iga_name = _normalize(iga["name"])
            iga_size = _normalize(iga.get("size", ""))
            iga_brand = _normalize(iga.get("brand", ""))

            # Gather candidates from same first-word group
            word = _get_first_significant_word(iga_name)
            candidates = tw_by_word.get(word, [])

            if not candidates:
                continue  # no candidates to match against

            # Use process.extract with token_sort_ratio for fast C++ matching
            # Convert candidates to {name: product} mapping
            cand_map = {_normalize(c["name"]): c for c in candidates}
            cand_names = list(cand_map.keys())

            # Get top N best matches via token_sort_ratio
            top_matches = process.extract(
                iga_name,
                cand_names,
                scorer=fuzz.token_sort_ratio,
                limit=min(TOP_N_CANDIDATES, len(cand_names)),
            )

            for tw_name, name_score in top_matches:
                if name_score < FUZZY_NAME_THRESHOLD:
                    continue

                confidence = name_score / 100.0
                tw = cand_map[tw_name]

                tw_size = _normalize(tw.get("size", ""))
                if iga_size and tw_size and iga_size == tw_size:
                    confidence += SIZE_BONUS

                tw_brand = _normalize(tw.get("brand", ""))
                if iga_brand and tw_brand and iga_brand == tw_brand:
                    confidence += BRAND_BONUS

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_id = tw["id"]
                    match_type = "fuzzy_name"

        if best_id and best_confidence >= min_confidence:
            statements.append((
                """INSERT OR REPLACE INTO product_matches
                   (iga_product_id, thriftway_product_id, match_type, confidence, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                [iga["id"], best_id, match_type, min(best_confidence, 1.0)]
            ))
            matched += 1
            if match_type == "upc_exact":
                upc_matches += 1
            else:
                fuzzy_matches += 1

    if statements:
        print(f"  Writing {len(statements)} matches to DB...")
        # Batch in groups of 500 to avoid huge payloads
        for batch_start in range(0, len(statements), 500):
            batch = statements[batch_start:batch_start + 500]
            batch_execute(batch)
            print(f"    Wrote batch {batch_start//500 + 1}/{(len(statements) + 499)//500}")

    print(f"\nDone! Matched {matched}/{len(iga_products)} IGA products")
    print(f"  UPC exact: {upc_matches}")
    print(f"  Fuzzy name: {fuzzy_matches}")
    return matched


if __name__ == "__main__":
    match_all()
