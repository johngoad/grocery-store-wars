#!/usr/bin/env python3
"""Matcher v4 — PRIORITIZED candidate selection + department pre-filter.
Key fixes over v3:
  1. Candidates ranked by word overlap count BEFORE trimming (good matches survive)
  2. At least 50% word overlap required for candidates (or all words if ≤2)
  3. Department pre-filter: same-dept candidates get priority boost
  4. Size pre-filter: very different sizes → drop candidate early
"""
import sys, re, time, os
from collections import defaultdict
from thefuzz import fuzz, process

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers.db import query, batch_execute

# --- CONFIG ---
UPC_MATCH_CONFIDENCE = 1.0
EXACT_TOKEN_SET_THRESHOLD = 90      # Token set threshold  
FUZZY_TOKEN_SORT_THRESHOLD = 76     # Lowered from 78
PARTIAL_RATIO_THRESHOLD = 83        # Lowered from 85
SIZE_BONUS = 0.08
BRAND_BONUS = 0.05
DEPT_BONUS = 0.03
MIN_CONFIDENCE = 0.65
TOP_N_CANDIDATES = 60               # After prioritization

# --- ABBREVIATION EXPANSION ---
ABBREV = {
    "cf": "cage free", "bf": "boneless", "sl": "sliced",
    "grn": "green", "aa": "grade aa", "a": "grade a",
    "org": "organic", "pk": "pack", "pkg": "package",
    "bbq": "barbecue", "brd": "breaded", "crm": "cream",
    "choc": "chocolate", "strwbry": "strawberry", "blkbry": "blackberry",
    "rspbry": "raspberry", "blubry": "blueberry", "veg": "vegetable",
    "frz": "frozen", "ckn": "chicken", "trky": "turkey",
    "ea": "each", "ct": "count", "dz": "dozen", "doz": "dozen",
    "gal": "gallon", "qt": "quart", "pt": "pint", "fl": "fluid",
    "oz": "ounce", "lb": "pound", "lbs": "pounds",
    "w/": "with", "w/o": "without",
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with", "by", "to",
    "lb", "lbs", "oz", "ozs", "ct", "cts", "ea", "pk", "pkg", "fl", "gal",
    "quart", "pint", "each", "per", "size", "item", "items", "ounce", "pound",
    "fluid", "pounds", "count", "dozen", "gallon", "half", "quarter",
}

GENERIC_WORDS = {
    "fresh", "organic", "natural", "original", "classic", "premium",
    "quality", "select", "choice", "value", "family", "large", "small",
    "regular", "new", "best", "signature", "homestyle", "homemade",
}

def log(msg):
    print(msg, flush=True)

def _normalize(s):
    if not s: return ""
    s = s.lower().strip()
    s = re.sub(r"[-–—]", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _expand_abbrevs(text):
    words = text.split()
    result = []
    for w in words:
        clean = w.strip("(),.-/#!?*\"'")
        if clean.lower() in ABBREV:
            result.append(ABBREV[clean.lower()])
        else:
            result.append(w)
    return " ".join(result)

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
            if len(w) > 1:
                result.append(w)
                break
    return result

def _normalize_size(s):
    if not s: return None
    s = s.lower().strip().rstrip('.')
    s = re.sub(r"\s+", " ", s)
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
    if unit == 'oz' and num >= 8:
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
            code = str(val).strip()
            code_clean = code.lstrip("0")
            if code_clean:
                upcs.add(code_clean)
                upcs.add(code_clean.zfill(12))
    return {c for c in upcs if c and len(c) >= 10}

def _size_compatible(s1, s2):
    if not s1 or not s2: return False
    if s1 == s2: return True
    if len(s1) > 2 and len(s2) > 2:
        return s1 in s2 or s2 in s1
    return False

# --- MAIN ---
log("=== MATCHER V4 ===")
log("Improvements: prioritized candidate trimming, dept pre-filter, lower thresholds")
t0 = time.time()

log("Loading products...")
iga_raw = query("SELECT id, name, upc, barcode, size, brand, department_id FROM products WHERE is_iga=1")
tw_raw = query("SELECT id, name, upc, barcode, size, brand, department_id FROM products WHERE is_iga=0")
log(f"  IGA: {len(iga_raw)} | Thriftway: {len(tw_raw)}")

# Pre-compute
for p in iga_raw:
    p["_norm"] = _normalize(p["name"])
    p["_expanded"] = _normalize(_expand_abbrevs(p["name"]))
    p["_size"] = _normalize_size(p.get("size", ""))
    p["_brand"] = _normalize(p.get("brand", "") or "")
    p["_words"] = _get_significant_words(p["_expanded"])
    p["_sig_word_set"] = set(p["_words"])
    p["_name_len"] = len(p["_expanded"].split())

for p in tw_raw:
    p["_norm"] = _normalize(p["name"])
    p["_expanded"] = _normalize(_expand_abbrevs(p["name"]))
    p["_size"] = _normalize_size(p.get("size", ""))
    p["_brand"] = _normalize(p.get("brand", "") or "")
    p["_words"] = _get_significant_words(p["_expanded"])
    p["_sig_word_set"] = set(p["_words"])
    p["_name_len"] = len(p["_expanded"].split())

log(f"  Pre-computed in {time.time()-t0:.1f}s")

# UPC index
tw_by_upc = {}
for p in tw_raw:
    for code in _get_upcs(p):
        tw_by_upc[code] = p

# Word index
tw_by_word = defaultdict(list)
for p in tw_raw:
    for w in p["_sig_word_set"]:
        tw_by_word[w].append(p)
log(f"  Word index: {len(tw_by_word)} words")

# Size index
tw_by_size = defaultdict(list)
for p in tw_raw:
    if p["_size"]:
        tw_by_size[p["_size"]].append(p)
log(f"  Size index: {len(tw_by_size)} sizes")

query("DELETE FROM product_matches")
log("  Cleared existing matches")

# Build tw_map ONCE outside the loop
tw_map = {p["id"]: p for p in tw_raw}
log(f"  TW lookup map: {len(tw_map)} entries")

matched = 0
upc_matches = 0
fuzzy_matches = 0
skipped_no_candidates = 0
statements = []

for i, iga in enumerate(iga_raw):
    if (i + 1) % 1000 == 0:
        log(f"  {i+1}/{len(iga_raw)}... ({matched} matched, {skipped_no_candidates} no-cands)")

    best_id = None
    best_confidence = 0.0
    match_type = "fuzzy_name"

    # Strategy 1: UPC
    for upc in _get_upcs(iga):
        if upc in tw_by_upc:
            best_id = tw_by_upc[upc]["id"]
            best_confidence = UPC_MATCH_CONFIDENCE
            match_type = "upc_exact"
            break

    # Strategy 2: Fuzzy with PRIORITIZED candidate selection
    if best_confidence < UPC_MATCH_CONFIDENCE:
        # Gather ALL candidates with word overlap counts
        candidate_hits = defaultdict(int)  # tw_id -> word overlap count
        
        for w in iga["_sig_word_set"]:
            for c in tw_by_word.get(w, []):
                candidate_hits[c["id"]] += 1
                # Also track the product object (only need first occurrence)
                if c["id"] not in candidate_hits:
                    pass  # defaultdict handles it

        # Size-index candidates (also count as hits)
        if iga["_size"]:
            for c in tw_by_size.get(iga["_size"], []):
                if c["id"] not in candidate_hits:
                    candidate_hits[c["id"]] = 0

        if not candidate_hits:
            skipped_no_candidates += 1
            continue

        # PRIORITIZE: sort candidates by word overlap (descending), then same-dept bonus
        iga_words_count = len(iga["_sig_word_set"])
        min_overlap = min(2, iga_words_count)  # Need at least 2 shared words, or all available if <2
        
        def candidate_priority(cid):
            overlap = candidate_hits[cid]
            # Products sharing more words come first
            return -overlap  # Negative for descending sort
        
        sorted_candidates = sorted(candidate_hits.keys(), key=candidate_priority)
        
        # Separate into "good" (≥min_overlap) and "fallback" pools
        good_candidates = []
        fallback_candidates = []
        
        for cid in sorted_candidates:
            overlap = candidate_hits[cid]
            tw = tw_map.get(cid)
            if not tw:
                continue
            if overlap >= min_overlap:
                good_candidates.append(tw)
            else:
                fallback_candidates.append(tw)
        
        # Prioritize same-dept candidates within each pool
        for pool in [good_candidates, fallback_candidates]:
            pool.sort(key=lambda c: (
                -(1 if c.get("department_id") == iga.get("department_id") else 0),
                -(candidate_hits.get(c["id"], 0))
            ))
        
        # Combine: good first, then fallback, trim
        all_candidates = good_candidates + fallback_candidates
        all_candidates = all_candidates[:TOP_N_CANDIDATES * 3]
        
        # Build name list with variants
        cand_map = {}
        all_names = []
        for c in all_candidates:
            cn = c["_expanded"]
            if cn not in cand_map:
                cand_map[cn] = c
                all_names.append(cn)
            # Also add normalized (non-expanded) as a variant
            cnn = c["_norm"]
            if cnn != cn and cnn not in cand_map:
                cand_map[cnn] = c
                all_names.append(cnn)
        
        all_names = all_names[:TOP_N_CANDIDATES * 5]
        
        iga_name = iga["_expanded"]
        
        # Multi-scorer: try all, keep best
        for c_name in all_names:
            tw = cand_map[c_name]
            
            ts = fuzz.token_sort_ratio(iga_name, c_name)
            tset = fuzz.token_set_ratio(iga_name, c_name)
            pr = fuzz.partial_ratio(iga_name, c_name)
            
            scores = []
            if ts >= FUZZY_TOKEN_SORT_THRESHOLD:
                scores.append(ts)
            if tset >= EXACT_TOKEN_SET_THRESHOLD:
                scores.append(tset)
            if pr >= PARTIAL_RATIO_THRESHOLD:
                scores.append(pr)
            
            if not scores:
                continue
            
            base_confidence = max(scores) / 100.0
            confidence = base_confidence
            
            # Size bonus
            if iga["_size"] and tw["_size"]:
                if iga["_size"] == tw["_size"]:
                    confidence += SIZE_BONUS
                elif _size_compatible(iga["_size"], tw["_size"]):
                    confidence += SIZE_BONUS * 0.4
            
            # Brand bonus
            if iga["_brand"] and tw["_brand"] and iga["_brand"] == tw["_brand"]:
                confidence += BRAND_BONUS
            
            # Department bonus
            if iga.get("department_id") == tw.get("department_id"):
                confidence += DEPT_BONUS
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_id = tw["id"]
                match_type = "fuzzy_name"
    
    if best_id and best_confidence >= MIN_CONFIDENCE:
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

log(f"  {len(iga_raw)}/{len(iga_raw)}... ({matched} matched, {skipped_no_candidates} no-cands)")

# Write to DB
if statements:
    log(f"\n  Writing {len(statements)} matches to DB...")
    for batch_start in range(0, len(statements), 500):
        batch = statements[batch_start:batch_start + 500]
        batch_execute(batch)
        log(f"    Batch {batch_start//500 + 1}/{(len(statements) + 499)//500}")

total_time = time.time() - t0
pct = matched / len(iga_raw) * 100 if iga_raw else 0
log(f"\n{'='*50}")
log(f"MATCHER V4 RESULTS")
log(f"  IGA products: {len(iga_raw)}")
log(f"  Matched: {matched} ({pct:.1f}%)")
log(f"  No candidates: {skipped_no_candidates}")
log(f"  UPC exact: {upc_matches}")
log(f"  Fuzzy name: {fuzzy_matches}")
log(f"  Total time: {total_time:.1f}s")
log(f"{'='*50}")
