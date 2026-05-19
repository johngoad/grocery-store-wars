#!/usr/bin/env python3
"""Sample rejected near-matches to understand what's holding them back."""
import sys, re, os
from collections import defaultdict
from thefuzz import fuzz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers.db import query

# Reuse the same normalize/expand logic
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

# Load unmatched IGA products (random sample)
iga_raw = query("""
    SELECT p.id, p.name, p.size, p.department_id, d.name as dept_name
    FROM products p LEFT JOIN departments d ON p.department_id = d.id
    WHERE p.is_iga=1 
    AND p.id NOT IN (SELECT iga_product_id FROM product_matches)
    ORDER BY RANDOM() LIMIT 30
""")

tw_raw = query("SELECT id, name FROM products WHERE is_iga=0")

# Build TW word index
tw_by_word = defaultdict(list)
for p in tw_raw:
    name = _normalize(_expand_abbrevs(p["name"]))
    words = _get_significant_words(name)
    for w in set(words):
        tw_by_word[w].append(p)

print("=== SAMPLING REJECTED IGA PRODUCTS (30 random) ===\n")
for iga in iga_raw:
    name = _normalize(_expand_abbrevs(iga["name"]))
    words = _get_significant_words(name)
    
    # Get candidates
    candidates = set()
    for w in set(words):
        for c in tw_by_word.get(w, []):
            candidates.add(c["id"])
    
    if not candidates:
        print(f"[{iga['dept_name'] or '?'}] {iga['name']}")
        print(f"  → 0 CANDIDATES (word: {' '.join(words)})")
        print()
        continue
    
    # Find best match
    best_score = 0
    best_name = ""
    best_scores = {}
    for cid in list(candidates)[:100]:  # Check first 100
        for c in tw_raw:
            if c["id"] == cid:
                cn = _normalize(_expand_abbrevs(c["name"]))
                ts = fuzz.token_sort_ratio(name, cn)
                tset = fuzz.token_set_ratio(name, cn)
                pr = fuzz.partial_ratio(name, cn)
                mx = max(ts, tset, pr)
                if mx > best_score:
                    best_score = mx
                    best_name = c["name"]
                    best_scores = {"ts": ts, "tset": tset, "pr": pr}
                break
    
    print(f"[{iga['dept_name'] or '?'}] {iga['name']} (size: {iga['size'] or 'none'})")
    print(f"  → {len(candidates)} candidates, best: {best_name}")
    print(f"    scores: ts={best_scores['ts']} tset={best_scores['tset']} pr={best_scores['pr']} max={best_score}")
    print()
