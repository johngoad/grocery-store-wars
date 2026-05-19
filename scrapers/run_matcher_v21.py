#!/usr/bin/env python3
"""Matcher v2.1 — first-word primary + multi-word fallback + v2 quality features."""
import sys, re, time, os
from collections import defaultdict
from thefuzz import fuzz, process

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers.db import query, batch_execute

UPC_MATCH_CONFIDENCE = 1.0
FUZZY_NAME_THRESHOLD = 78
SIZE_BONUS = 0.08
BRAND_BONUS = 0.05
TOP_N_CANDIDATES = 15  # Fewer needed with first-word index
MIN_CONFIDENCE = 0.65
MIN_FALLBACK_CANDIDATES = 3  # Trigger multi-word fallback if fewer than this

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

def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

def _normalize(s):
    if not s: return ""
    return s.lower().strip().replace("'s", "s").replace("  ", " ")

def _get_first_significant_word(name: str) -> str:
    """Get first significant word (not stop word, not generic)."""
    words = name.split()
    for w in words:
        w = w.strip("(),.-/#!?*\"'")
        if w and len(w) > 1 and w not in STOP_WORDS and w not in GENERIC_WORDS:
            return w
    # Fallback: any non-trivial word
    for w in words:
        w = w.strip("(),.-/#!?*\"'")
        if len(w) > 1 and w not in STOP_WORDS:
            return w
    return words[0].strip("(),.-") if words else ""

def _get_all_significant_words(name: str) -> list[str]:
    """Return ALL significant words for multi-word fallback index."""
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

def _collect_candidates(iga_name, iga_size, iga_brand, tw_by_first_word, tw_by_all_words, tw_by_size):
    """Collect candidates: first-word primary, multi-word fallback if too few."""
    candidate_ids = set()
    candidates = []

    # Primary: first significant word index
    first_word = _get_first_significant_word(iga_name)
    for c in tw_by_first_word.get(first_word, []):
        if c["id"] not in candidate_ids:
            candidate_ids.add(c["id"])
            candidates.append(c)

    # Fallback: multi-word index if too few candidates
    if len(candidates) < MIN_FALLBACK_CANDIDATES:
        fallback_count = 0
        all_words = _get_all_significant_words(iga_name)
        for w in all_words:
            if w == first_word: continue
            for c in tw_by_all_words.get(w, []):
                if c["id"] not in candidate_ids:
                    candidate_ids.add(c["id"])
                    candidates.append(c)
                    fallback_count += 1
        if fallback_count:
            pass  # log(f"    Fallback: +{fallback_count} candidates for '{iga_name[:30]}'")

    # Size-index candidates
    if iga_size:
        for c in tw_by_size.get(iga_size, []):
            if c["id"] not in candidate_ids:
                candidate_ids.add(c["id"])
                candidates.append(c)

    return candidates

def _score_candidates(iga_name, iga_size, iga_brand, candidates):
    """Score all candidates and return best match."""
    if not candidates:
        return None, 0.0, "fuzzy_name"

    cand_map = {}
    priority_candidates = []
    other_candidates = []

    for c in candidates:
        cn = _normalize(c["name"])
        cs = _normalize_size(c.get("size", ""))
        cb = _normalize(c.get("brand", "") or "")
        cand_map[cn] = c
        priority = 0
        if iga_brand and cb and iga_brand == cb: priority += 2
        if iga_size and cs and iga_size == cs: priority += 1
        (priority_candidates if priority > 0 else other_candidates).append(cn)

    all_cand_names = priority_candidates + other_candidates
    all_cand_names = all_cand_names[:TOP_N_CANDIDATES * 2]

    if not all_cand_names:
        return None, 0.0, "fuzzy_name"

    top_matches = process.extract(
        iga_name, all_cand_names,
        scorer=fuzz.token_sort_ratio,
        limit=min(TOP_N_CANDIDATES, len(all_cand_names)),
    )

    best_id = None
    best_confidence = 0.0

    for tw_name, name_score in top_matches:
        if name_score < FUZZY_NAME_THRESHOLD: continue
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

    return best_id, best_confidence, "fuzzy_name"


log("=== Matcher v2.1: first-word primary + multi-word fallback ===")

log("Loading products...")
t0 = time.time()
iga_products = query("SELECT id, name, upc, barcode, size, brand FROM products WHERE is_iga=1")
tw_products = query("SELECT id, name, upc, barcode, size, brand FROM products WHERE is_iga=0")
log(f"  Loaded {len(iga_products)} IGA + {len(tw_products)} TW in {time.time()-t0:.1f}s")

# UPC index
t1 = time.time()
tw_by_upc = {}
for p in tw_products:
    for code in _get_upcs(p):
        tw_by_upc[code] = p
log(f"  UPC index: {len(tw_by_upc)} codes ({time.time()-t1:.1f}s)")

# First-word index (primary)
t1 = time.time()
tw_by_first_word = defaultdict(list)
for p in tw_products:
    w = _get_first_significant_word(_normalize(p["name"]))
    tw_by_first_word[w].append(p)
log(f"  First-word index: {len(tw_by_first_word)} words ({time.time()-t1:.1f}s)")

# All-words index (fallback)
t1 = time.time()
tw_by_all_words = defaultdict(list)
for p in tw_products:
    words = _get_all_significant_words(_normalize(p["name"]))
    for w in set(words):
        tw_by_all_words[w].append(p)
log(f"  All-words index: {len(tw_by_all_words)} words ({time.time()-t1:.1f}s)")

# Size index
t1 = time.time()
tw_by_size = defaultdict(list)
for p in tw_products:
    ns = _normalize_size(p.get("size", ""))
    if ns:
        tw_by_size[ns].append(p)
log(f"  Size index: {len(tw_by_size)} sizes ({time.time()-t1:.1f}s)")

# Clear existing
query("DELETE FROM product_matches")
log("  Cleared existing matches")

matched = 0
upc_matches = 0
fuzzy_matches = 0
fallback_used = 0
statements = []

for i, iga in enumerate(iga_products):
    if (i + 1) % 1000 == 0:
        elapsed = time.time() - t0
        log(f"  {i+1}/{len(iga_products)}... ({matched} matched, FB={fallback_used}, {elapsed:.0f}s)")

    iga_name = _normalize(iga["name"])
    iga_size = _normalize_size(iga.get("size", ""))
    iga_brand = _normalize(iga.get("brand", "") or "")

    best_id = None
    best_confidence = 0.0
    match_type = "fuzzy_name"

    # Strategy 1: UPC exact
    for upc in _get_upcs(iga):
        if upc in tw_by_upc:
            best_id = tw_by_upc[upc]["id"]
            best_confidence = UPC_MATCH_CONFIDENCE
            match_type = "upc_exact"
            break

    # Strategy 2: Fuzzy matching (first-word primary, multi-word fallback)
    if best_confidence < UPC_MATCH_CONFIDENCE:
        candidates = _collect_candidates(
            iga_name, iga_size, iga_brand,
            tw_by_first_word, tw_by_all_words, tw_by_size
        )

        # Track fallback usage
        first_word = _get_first_significant_word(iga_name)
        first_word_count = len(tw_by_first_word.get(first_word, []))
        if first_word_count < MIN_FALLBACK_CANDIDATES and len(candidates) > first_word_count:
            fallback_used += 1

        best_id, best_confidence, match_type = _score_candidates(
            iga_name, iga_size, iga_brand, candidates
        )

    if best_id and best_confidence >= MIN_CONFIDENCE:
        statements.append((
            """INSERT OR REPLACE INTO product_matches
               (iga_product_id, thriftway_product_id, match_type, confidence, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            [iga["id"], best_id, match_type, min(best_confidence, 1.0)]
        ))
        matched += 1
        if match_type == "upc_exact": upc_matches += 1
        else: fuzzy_matches += 1

elapsed = time.time() - t0
log(f"  {len(iga_products)}/{len(iga_products)}... ({matched} matched, FB={fallback_used}, {elapsed:.0f}s)")

# Write to DB
if statements:
    log(f"  Writing {len(statements)} matches to DB...")
    for batch_start in range(0, len(statements), 500):
        batch = statements[batch_start:batch_start + 500]
        batch_execute(batch)
    log("  Done writing")

pct = matched/len(iga_products)*100
log(f"\n{'='*50}")
log(f"RESULTS: {matched}/{len(iga_products)} matches ({pct:.1f}%)")
log(f"  UPC exact: {upc_matches}")
log(f"  Fuzzy name: {fuzzy_matches}")
log(f"  Fallback triggers: {fallback_used}")
log(f"  Total time: {elapsed:.0f}s")
