"""
Product matcher — cross-store matching via name similarity.
Strategy:
  1. Exact name match (normalized) → confidence 1.0
  2. Token-set intersection (Jaccard similarity) → confidence 0.7-0.99
  3. FuzzyWuzzy partial ratio → fallback for singletons

Writes to product_matches table.
"""
import sys, os, re, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.db import execute, query, batch_execute

# --- Name normalization ---

_UNITS = re.compile(
    r'\b(oz|lbs?|lb|each|ea|per lb|per oz|count|ct|pack|pk|'
    r'fl\.?\s*oz|gallon|gal|quart|qt|pint|pt|dozen|dz|'
    r'bag|box|can|jar|bottle|btl|roll|loaf|loaves)\b',
    re.IGNORECASE
)
_DIMENSIONS = re.compile(r'\b\d+\.?\d*\s*(oz|lbs?|g|ml|ct|each|ea|pk|roll)\b', re.IGNORECASE)
_BRAND_PREFIXES = [
    "organic", "365 organic", "365", "whole foods", "trader joe's", "tj's",
    "kirkland", "great value", "market pantry", "good & gather",
    "signature select", "simply balanced", "simply nature", "open nature",
    "private selection", "kroger", "safeway", "albertsons",
    "member's mark", "sam's choice", "first street", "best choice",
    "always save", "clover valley", "essential everyday", "food club",
    "giant", "stop & shop", "shoprite", "publix", "heinen's",
    "central market", "heb", "meijer", "winco", "woodman's",
]

def normalize(name: str) -> str:
    """Normalize product name for comparison."""
    if not name:
        return ""
    s = name.lower().strip()
    
    # Remove leading organic/ brand prefixes
    for bp in _BRAND_PREFIXES:
        if s.startswith(bp + " "):
            s = s[len(bp)+1:]
    
    # Strip size/unit patterns from end
    s = _UNITS.sub('', s)
    s = _DIMENSIONS.sub('', s)
    
    # Remove special chars, collapse whitespace
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    
    return s

# --- Matching ---

def jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)

def match_products(iga_products: list[dict], thriftway_products: list[dict]) -> list[dict]:
    """Match IGA products to Thriftway products. Returns list of match dicts."""
    
    # Build lookup structures
    print(f"Matching {len(iga_products)} IGA vs {len(thriftway_products)} Thriftway products...")
    
    # Normalize all names, tokenize
    iga_map = {}  # normalized_name -> list of product ids
    iga_tokens = {}  # id -> set of tokens
    iga_id_to_name = {}  # id -> original name
    
    for p in iga_products:
        norm = normalize(p['name'])
        if norm:
            iga_map.setdefault(norm, []).append(p['id'])
            iga_tokens[p['id']] = set(norm.split())
            iga_id_to_name[p['id']] = p['name']
    
    thriftway_map = {}
    thriftway_tokens = {}
    thriftway_id_to_name = {}
    
    for p in thriftway_products:
        norm = normalize(p['name'])
        if norm:
            thriftway_map.setdefault(norm, []).append(p['id'])
            thriftway_tokens[p['id']] = set(norm.split())
            thriftway_id_to_name[p['id']] = p['name']
    
    matches = []
    thriftway_matched = set()
    
    # Phase 1: Exact normalized name match
    exact_count = 0
    for norm_name, iga_ids in iga_map.items():
        if norm_name in thriftway_map:
            for tid in thriftway_map[norm_name]:
                if tid in thriftway_matched:
                    continue
                for iid in iga_ids:
                    matches.append({
                        'iga_product_id': iid,
                        'thriftway_product_id': tid,
                        'match_type': 'exact',
                        'confidence': 1.0,
                        'iga_name': iga_id_to_name[iid],
                        'thriftway_name': thriftway_id_to_name[tid],
                    })
                    thriftway_matched.add(tid)
                    exact_count += 1
    
    print(f"  Exact matches: {exact_count}")
    
    # Phase 2: Token-set intersection (Jaccard)
    token_match_count = 0
    
    # Build a token-to-thriftway index for efficiency
    token_index = defaultdict(set)
    for tid, tokens in thriftway_tokens.items():
        if tid in thriftway_matched:
            continue
        for token in tokens:
            token_index[token].add(tid)
    
    for iid, iga_tok in iga_tokens.items():
        if len(iga_tok) < 2:  # Skip single-token names
            continue
        
        # Find candidates that share at least one token
        candidates = set()
        for token in iga_tok:
            candidates |= token_index.get(token, set())
        
        candidates -= thriftway_matched
        
        for tid in candidates:
            thrift_tok = thriftway_tokens[tid]
            sim = jaccard(iga_tok, thrift_tok)
            
            if sim >= 0.6:  # 60% token overlap
                exists = any(
                    m['iga_product_id'] == iid and m['thriftway_product_id'] == tid
                    for m in matches
                )
                if not exists:
                    matches.append({
                        'iga_product_id': iid,
                        'thriftway_product_id': tid,
                        'match_type': 'token_similarity',
                        'confidence': round(sim, 3),
                        'iga_name': iga_id_to_name[iid],
                        'thriftway_name': thriftway_id_to_name[tid],
                    })
                    thriftway_matched.add(tid)
                    token_match_count += 1
    
    print(f"  Token similarity matches: {token_match_count}")
    
    return matches


# --- Save to DB ---

def save_matches(matches: list[dict]):
    """Write matches to product_matches table, skipping duplicates."""
    if not matches:
        print("No matches to save.")
        return
    
    # Clear existing matches
    execute("DELETE FROM product_matches")
    
    # Batch insert
    statements = []
    for m in matches:
        sql = """
            INSERT INTO product_matches 
            (iga_product_id, thriftway_product_id, match_type, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """
        statements.append((
            sql,
            [m['iga_product_id'], m['thriftway_product_id'], m['match_type'], m['confidence']]
        ))
    
    batch_execute(statements)
    
    # Verify
    cnt = query("SELECT COUNT(*) as cnt FROM product_matches")[0]['cnt']
    types = query("SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type")
    print(f"\nSaved {cnt} matches:")
    for t in types:
        print(f"  {t['match_type']}: {t['cnt']}")


# --- Main ---

def main():
    start = time.time()
    
    print("Loading IGA products...")
    iga_products = query(
        "SELECT id, name FROM products WHERE store_id='iga-vashon'"
    )
    
    print("Loading Thriftway products...")
    thriftway_products = query(
        "SELECT id, name FROM products WHERE store_id='thriftway-vashon'"
    )
    
    matches = match_products(iga_products, thriftway_products)
    save_matches(matches)
    
    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.1f}s")
    
    # Print some sample matches
    samples = query("""
        SELECT pm.match_type, pm.confidence, 
               p_iga.name as iga_name, p_thrift.name as thriftway_name,
               p_iga.price as iga_price, p_thrift.price as thriftway_price
        FROM product_matches pm
        JOIN products p_iga ON pm.iga_product_id = p_iga.id
        JOIN products p_thrift ON pm.thriftway_product_id = p_thrift.id
        ORDER BY pm.confidence DESC
        LIMIT 10
    """)
    print("\n=== Top 10 matches ===")
    for s in samples:
        diff = s['iga_price'] - s['thriftway_price'] if s['iga_price'] and s['thriftway_price'] else 0
        sign = "+" if diff > 0 else ""
        print(f"  [{s['match_type']} {s['confidence']:.2f}] {s['iga_name'][:40]} | {s['thriftway_name'][:40]}")
        if s['iga_price'] and s['thriftway_price']:
            print(f"    IGA: ${s['iga_price']}  Thriftway: ${s['thriftway_price']}  diff: {sign}{diff:.2f}")


if __name__ == '__main__':
    main()
