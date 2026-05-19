"""Dump products from Turso to JSON using shell, then run matcher v2."""
import subprocess, json, sys
from collections import defaultdict
from thefuzz import fuzz, process

# ── Copy of matcher v2 functions, fast local matching ──

UPC_MATCH_CONFIDENCE = 1.0
FUZZY_NAME_THRESHOLD = 78
SIZE_BONUS = 0.08
BRAND_BONUS = 0.05
TOP_N_CANDIDATES = 30

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with", "by",
    "lb", "lbs", "oz", "ozs", "ct", "cts", "ea", "pk", "pkg", "fl", "gal",
    "quart", "pint", "each", "per", "size", "item", "items",
}
GENERIC_WORDS = {
    "fresh", "organic", "natural", "original", "classic", "premium",
    "quality", "select", "choice", "value", "family", "large", "small",
    "regular", "new", "best", "signature", "homestyle", "homemade",
}

import re

def _normalize(s):
    if not s: return ""
    return s.lower().strip().replace("'s", "s").replace("  ", " ")

def _get_significant_words(name):
    words = name.split()
    result = []
    for w in words:
        w = w.strip("(),.-/#!?*\"'")
        if w and len(w) > 1 and w not in STOP_WORDS and w not in GENERIC_WORDS:
            result.append(w)
    if not result and words:
        for w in words:
            w = w.strip("(),.-/#!?*\"'")
            if len(w) > 1: result.append(w); break
    return result

def _normalize_size(s):
    if not s: return None
    s = s.lower().strip().rstrip('.')
    m = re.match(r'^([\d.]+)\s*(fl\s*)?(oz|ct|ea|gal|qt|pt|lb|lbs|ml|l|g|kg)(s)?$', s)
    if not m: return s
    num = float(m.group(1))
    unit = m.group(3)
    if unit in ('lb', 'lbs'): unit = 'lb'
    if unit == 'ea': unit = 'ct'
    if unit == 'gal':
        if num == 0.5: return 'half gallon'
        if num == 1: return 'gallon'
        if num == 0.25: return 'quart'
    if unit == 'fl oz' or (unit == 'oz' and num >= 8):
        if num == 64: return 'half gallon'
        if num == 32: return 'quart'
        if num == 16: return 'pint'
        if num == 8: return 'cup'
    if unit in ('qt', 'quart'):
        if num == 1: return 'quart'
        if num == 0.5: return 'pint'
    if unit in ('pt', 'pint'):
        if num == 1: return 'pint'
        if num == 0.5: return 'cup'
    if unit == 'ct' and num == 12: return 'dozen'
    if unit == 'ct' and num == 6: return 'half dozen'
    if unit == 'ct' and num == 18: return 'dozen and half'
    if unit == 'oz': return f'{num} oz'
    return s

def _get_upcs(p):
    upcs = set()
    for field in ["upc", "barcode"]:
        val = p.get(field)
        if val:
            code = str(val).strip().lstrip("0")
            upcs.add(code)
            upcs.add(code.zfill(12))
    return {c for c in upcs if c and len(c) >= 10}

def dump_products(is_iga):
    """Dump products from Turso via CLI shell."""
    where = "is_iga=1" if is_iga else "is_iga=0"
    sql = f"SELECT id, name, upc, barcode, size, brand FROM products WHERE {where};"
    result = subprocess.run(
        ["turso", "db", "shell", "grocery-store-wars", "--json", sql],
        capture_output=True, text=True, timeout=60
    )
    data = json.loads(result.stdout)
    # results is a list of {columns: [...], rows: [[...], ...], ...}
    products = []
    for r in data.get("results", []):
        cols = r.get("columns", [])
        for row in r.get("rows", []):
            products.append(dict(zip(cols, row)))
    return products


def write_matches(matches):
    """Write matches via Turso CLI SQL."""
    if not matches:
        return
    # Write as SQL dump
    lines = ["DELETE FROM product_matches;"]
    for m in matches:
        lines.append(
            f"INSERT OR REPLACE INTO product_matches "
            f"(iga_product_id, thriftway_product_id, match_type, confidence, updated_at) "
            f"VALUES ('{m[0]}', '{m[1]}', '{m[2]}', {m[3]:.3f}, datetime('now'));"
        )
    sql_file = "/tmp/matches.sql"
    with open(sql_file, "w") as f:
        f.write("\n".join(lines))
    
    subprocess.run(
        ["turso", "db", "shell", "grocery-store-wars", f".read {sql_file}"],
        capture_output=True, timeout=60
    )
    print(f"  Wrote {len(matches)} matches to DB")


def match_products(iga_products, tw_products):
    """Run multi-word indexed matching on local data."""
    # UPC index
    tw_by_upc = {}
    for p in tw_products:
        for code in _get_upcs(p):
            tw_by_upc[code] = p
    print(f"  UPC index: {len(tw_by_upc)}")

    # Multi-word index
    tw_by_word = defaultdict(list)
    for p in tw_products:
        words = _get_significant_words(_normalize(p["name"]))
        for w in set(words):
            tw_by_word[w].append(p)
    print(f"  Word index: {len(tw_by_word)} words")

    # Size index
    tw_by_size = defaultdict(list)
    for p in tw_products:
        ns = _normalize_size(p.get("size", ""))
        if ns:
            tw_by_size[ns].append(p)
    print(f"  Size index: {len(tw_by_size)} sizes")

    all_matches = []
    matched = 0
    upc_matches = 0
    fuzzy_matches = 0

    for i, iga in enumerate(iga_products):
        if (i + 1) % 1000 == 0:
            print(f"  {i+1}/{len(iga_products)}... ({matched} matched)")

        best_id = None
        best_confidence = 0.0
        match_type = "fuzzy_name"

        # UPC exact
        for upc in _get_upcs(iga):
            if upc in tw_by_upc:
                best_id = tw_by_upc[upc]["id"]
                best_confidence = UPC_MATCH_CONFIDENCE
                match_type = "upc_exact"
                break

        # Fuzzy name
        if best_confidence < UPC_MATCH_CONFIDENCE:
            iga_name = _normalize(iga["name"])
            iga_size = _normalize_size(iga.get("size", ""))
            iga_brand = _normalize(iga.get("brand", "") or "")

            # Gather candidates from all words
            iga_words = _get_significant_words(iga_name)
            candidate_ids = set()
            candidates = []

            for w in iga_words:
                for c in tw_by_word.get(w, []):
                    if c["id"] not in candidate_ids:
                        candidate_ids.add(c["id"])
                        candidates.append(c)

            if iga_size:
                for c in tw_by_size.get(iga_size, []):
                    if c["id"] not in candidate_ids:
                        candidate_ids.add(c["id"])
                        candidates.append(c)

            if not candidates:
                continue

            cand_map = {}
            priority_candidates = []
            other_candidates = []

            for c in candidates:
                cn = _normalize(c["name"])
                cs = _normalize_size(c.get("size", ""))
                cb = _normalize(c.get("brand", "") or "")
                cand_map[cn] = c
                priority = 0
                if iga_brand and cb and iga_brand == cb:
                    priority += 2
                if iga_size and cs and iga_size == cs:
                    priority += 1
                (priority_candidates if priority > 0 else other_candidates).append(cn)

            all_cand_names = priority_candidates + other_candidates
            all_cand_names = all_cand_names[:TOP_N_CANDIDATES * 3]

            if not all_cand_names:
                continue

            top_matches = process.extract(
                iga_name, all_cand_names,
                scorer=fuzz.token_sort_ratio,
                limit=min(TOP_N_CANDIDATES, len(all_cand_names)),
            )

            for tw_name, name_score in top_matches:
                if name_score < FUZZY_NAME_THRESHOLD:
                    continue
                confidence = name_score / 100.0
                tw = cand_map[tw_name]

                tw_size = _normalize_size(tw.get("size", ""))
                if iga_size and tw_size:
                    if iga_size == tw_size:
                        confidence += SIZE_BONUS
                    elif len(iga_size) > 2 and len(tw_size) > 2 and (
                        iga_size in tw_size or tw_size in iga_size
                    ):
                        confidence += SIZE_BONUS * 0.5

                tw_brand = _normalize(tw.get("brand", "") or "")
                if iga_brand and tw_brand and iga_brand == tw_brand:
                    confidence += BRAND_BONUS

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_id = tw["id"]
                    match_type = "fuzzy_name"

        if best_id and best_confidence >= 0.65:
            all_matches.append((iga["id"], best_id, match_type, min(best_confidence, 1.0)))
            matched += 1
            if match_type == "upc_exact":
                upc_matches += 1
            else:
                fuzzy_matches += 1

    print(f"\nDone! Matched {matched}/{len(iga_products)} ({matched/len(iga_products)*100:.1f}%)")
    print(f"  UPC exact: {upc_matches}")
    print(f"  Fuzzy name: {fuzzy_matches}")
    return all_matches


if __name__ == "__main__":
    print("Dumping IGA products...")
    iga = dump_products(True)
    print(f"  {len(iga)} IGA products")

    print("Dumping Thriftway products...")
    tw = dump_products(False)
    print(f"  {len(tw)} Thriftway products")

    print("Matching...")
    matches = match_products(iga, tw)

    print("Writing to DB...")
    write_matches(matches)

    print("DONE!")
