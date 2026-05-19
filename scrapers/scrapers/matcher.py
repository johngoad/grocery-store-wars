"""Product matcher v2 — multi-word index, size normalization, smarter matching."""
import re
from collections import defaultdict
from thefuzz import fuzz, process
from scrapers.db import query, batch_execute

UPC_MATCH_CONFIDENCE = 1.0
FUZZY_NAME_THRESHOLD = 78  # Lower: multi-word index + size bonus catches real matches
SIZE_BONUS = 0.08
BRAND_BONUS = 0.05
TOP_N_CANDIDATES = 30  # Fewer candidates needed with better indexing

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with", "by",
    "lb", "lbs", "oz", "ozs", "ct", "cts", "ea", "pk", "pkg", "fl", "gal",
    "quart", "pint", "each", "per", "size", "item", "items",
}
# Words that are too generic to use as index keys
GENERIC_WORDS = {
    "fresh", "organic", "natural", "original", "classic", "premium",
    "quality", "select", "choice", "value", "family", "large", "small",
    "regular", "new", "best", "signature", "homestyle", "homemade",
}

def _normalize(s):
    if not s:
        return ""
    return s.lower().strip().replace("'s", "s").replace("  ", " ")

def _get_significant_words(name: str) -> list[str]:
    """Return all significant words (not stop words, not generic, >1 char)."""
    words = name.split()
    result = []
    for w in words:
        w = w.strip("(),.-/#!?*\"'")
        if w and len(w) > 1 and w not in STOP_WORDS and w not in GENERIC_WORDS:
            result.append(w)
    if not result and words:
        # Fallback: use first non-trivial word
        for w in words:
            w = w.strip("(),.-/#!?*\"'")
            if len(w) > 1:
                result.append(w)
                break
    return result

def _normalize_size(size_str: str) -> str | None:
    """Normalize size to a canonical form for comparison.
    
    Converts:
        "0.5 gal" -> "half gallon"
        "12 ct" -> "dozen"
        "64 fl oz" -> "half gallon"
        "1 qt" -> "quart"
        "1 pt" -> "pint"
        "6 oz." -> "6 oz"
        "18ct" -> "18 ct"
        "1.2 oz" -> "1.2 oz" (kept as-is)
    
    Returns None if size_str is empty/unparseable.
    """
    if not size_str:
        return None
    
    s = size_str.lower().strip().rstrip('.')
    # Split number from unit
    m = re.match(r'^([\d.]+)\s*(fl\s*)?(oz|ct|ea|gal|qt|pt|lb|lbs|ml|l|g|kg)(s)?$', s)
    if not m:
        return s  # Return as-is for non-standard formats
    
    num = float(m.group(1))
    unit = m.group(3)
    
    # Standardize units
    if unit in ('lb', 'lbs'):
        unit = 'lb'
    if unit == 'ea':
        unit = 'ct'
    
    # Size equivalences
    if unit == 'gal':
        if num == 0.5:
            return 'half gallon'
        if num == 1:
            return 'gallon'
        if num == 0.25:
            return 'quart'
    
    if unit == 'fl oz' or (unit == 'oz' and num >= 8):
        if num == 64:
            return 'half gallon'
        if num == 32:
            return 'quart'
        if num == 16:
            return 'pint'
        if num == 8:
            return 'cup'
    
    if unit == 'qt' or unit == 'quart':
        if num == 1:
            return 'quart'
        if num == 0.5:
            return 'pint'
    
    if unit == 'pt' or unit == 'pint':
        if num == 1:
            return 'pint'
        if num == 0.5:
            return 'cup'
    
    if unit == 'ct' and num == 12:
        return 'dozen'
    if unit == 'ct' and num == 6:
        return 'half dozen'
    if unit == 'ct' and num == 18:
        return 'dozen and half'
    
    if unit == 'oz':
        return f'{num} oz'
    
    return s

def _get_upcs(product: dict) -> set:
    upcs = set()
    for field in ["upc", "barcode"]:
        val = product.get(field)
        if val:
            code = str(val).strip().lstrip("0")
            upcs.add(code)
            upcs.add(code.zfill(12))
    return {c for c in upcs if c and len(c) >= 10}

def match_all(min_confidence: float = 0.65):
    print("Loading products...")
    iga_products = query(
        "SELECT id, name, upc, barcode, size, brand, department_id FROM products WHERE is_iga=1"
    )
    tw_products = query(
        "SELECT id, name, upc, barcode, size, brand, department_id FROM products WHERE is_iga=0"
    )
    print(f"  IGA: {len(iga_products)} | Thriftway: {len(tw_products)}")

    # Build UPC index
    tw_by_upc = {}
    for p in tw_products:
        for code in _get_upcs(p):
            tw_by_upc[code] = p
    print(f"  UPC index: {len(tw_by_upc)} codes")

    # Build MULTI-WORD inverted index
    # Every significant word in a product name maps back to that product
    tw_by_word = defaultdict(list)
    for p in tw_products:
        words = _get_significant_words(_normalize(p["name"]))
        dedup_words = set(words)  # Don't index same product under same word multiple times
        for w in dedup_words:
            tw_by_word[w].append(p)
    print(f"  Word index: {len(tw_by_word)} unique words, {sum(len(v) for v in tw_by_word.values())} total entries")

    # Also index by normalized size for size-based candidate collection
    tw_by_size = defaultdict(list)
    for p in tw_products:
        ns = _normalize_size(p.get("size", ""))
        if ns:
            tw_by_size[ns].append(p)
    print(f"  Size index: {len(tw_by_size)} unique sizes")

    # Clear existing matches (so we start fresh)
    query("DELETE FROM product_matches")
    print("  Cleared existing matches")

    matched = 0
    upc_matches = 0
    fuzzy_matches = 0
    statements = []

    for i, iga in enumerate(iga_products):
        if (i + 1) % 1000 == 0:
            print(f"  Processing {i+1}/{len(iga_products)}... ({matched} matched so far)")

        best_id = None
        best_confidence = 0.0
        match_type = "fuzzy_name"

        # Strategy 1: Exact UPC match
        for upc in _get_upcs(iga):
            if upc in tw_by_upc:
                best_id = tw_by_upc[upc]["id"]
                best_confidence = UPC_MATCH_CONFIDENCE
                match_type = "upc_exact"
                break

        # Strategy 2: Multi-word fuzzy matching
        if best_confidence < UPC_MATCH_CONFIDENCE:
            iga_name = _normalize(iga["name"])
            iga_size = _normalize_size(iga.get("size", ""))
            iga_brand = _normalize(iga.get("brand", "") or "")

            # Gather candidates from ALL significant words
            iga_words = _get_significant_words(iga_name)
            candidate_ids = set()
            candidates = []

            # Phase A: Word-index candidates
            for w in iga_words:
                for c in tw_by_word.get(w, []):
                    if c["id"] not in candidate_ids:
                        candidate_ids.add(c["id"])
                        candidates.append(c)

            # Phase B: Size-index candidates (if IGA has a size)
            if iga_size:
                for c in tw_by_size.get(iga_size, []):
                    if c["id"] not in candidate_ids:
                        candidate_ids.add(c["id"])
                        candidates.append(c)

            # If no candidates from word index, fall back to broad search
            if not candidates:
                continue

            # Build candidate map for process.extract
            cand_map = {}
            # Prioritize candidates with brand match or size match
            priority_candidates = []
            other_candidates = []

            for c in candidates:
                cn = _normalize(c["name"])
                cs = _normalize_size(c.get("size", ""))
                cb = _normalize(c.get("brand", "") or "")
                cand_map[cn] = c

                # Score for prioritizing
                priority = 0
                if iga_brand and cb and iga_brand == cb:
                    priority += 2
                if iga_size and cs and iga_size == cs:
                    priority += 1

                if priority > 0:
                    priority_candidates.append(cn)
                else:
                    other_candidates.append(cn)

            # Limit candidates: prioritize brand+sized matches, then fill with others
            all_cand_names = priority_candidates + other_candidates
            all_cand_names = all_cand_names[:TOP_N_CANDIDATES * 3]  # Broader pool

            if not all_cand_names:
                continue

            # Token sort ratio is better for name comparisons
            top_matches = process.extract(
                iga_name,
                all_cand_names,
                scorer=fuzz.token_sort_ratio,
                limit=min(TOP_N_CANDIDATES, len(all_cand_names)),
            )

            for tw_name, name_score in top_matches:
                if name_score < FUZZY_NAME_THRESHOLD:
                    continue

                confidence = name_score / 100.0
                tw = cand_map[tw_name]

                # Size bonus
                tw_size = _normalize_size(tw.get("size", ""))
                if iga_size and tw_size:
                    if iga_size == tw_size:
                        confidence += SIZE_BONUS
                    elif len(iga_size) > 2 and len(tw_size) > 2 and (
                        iga_size in tw_size or tw_size in iga_size
                    ):
                        confidence += SIZE_BONUS * 0.5  # Partial size match

                # Brand bonus
                tw_brand = _normalize(tw.get("brand", "") or "")
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
        for batch_start in range(0, len(statements), 500):
            batch = statements[batch_start:batch_start + 500]
            batch_execute(batch)
            print(f"    Batch {batch_start//500 + 1}/{(len(statements) + 499)//500}")

    print(f"\nDone! Matched {matched}/{len(iga_products)} IGA products ({matched/len(iga_products)*100:.1f}%)")
    print(f"  UPC exact: {upc_matches}")
    print(f"  Fuzzy name: {fuzzy_matches}")
    return matched


if __name__ == "__main__":
    match_all()
