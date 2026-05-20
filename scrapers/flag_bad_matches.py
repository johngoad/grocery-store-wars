#!/usr/bin/env python3
"""Flag poor-quality product_matches for dashboard filtering.
Detects: multi-pack vs single, spice jar vs per-lb, category conflicts, short-name mismatches, size ratio.
Run after any matcher re-run to clean the results.
Uses batch pipeline calls — single HTTP round-trip for all flags.
"""
import re, os, httpx, sys
from dotenv import load_dotenv

load_dotenv(os.path.expanduser('~/workspace/grocery-store-wars/frontend/.env.local'))

DB_URL = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://")
DB_TOKEN = os.environ["TURSO_AUTH_TOKEN"]

client = httpx.Client(base_url=DB_URL, headers={"Authorization": f"Bearer {DB_TOKEN}"}, timeout=30)

def execute(sql, params=None):
    args = []
    if params:
        for p in params:
            if p is None: args.append({"type": "null"})
            elif isinstance(p, (int, float)): args.append({"type": "integer" if isinstance(p, int) else "float", "value": str(p)})
            else: args.append({"type": "text", "value": str(p)})
    resp = client.post("/v2/pipeline", json={"requests": [{"type": "execute", "stmt": {"sql": sql, "args": args} if args else {"sql": sql}}]})
    resp.raise_for_status()
    r0 = resp.json()["results"][0]
    if r0.get("type") == "error":
        print(f"SQL ERROR: {r0.get('error', {}).get('message', 'unknown')}", file=sys.stderr)
        return None
    return r0["response"]["result"]

def query(sql, params=None):
    result = execute(sql, params)
    if not result or "rows" not in result: return []
    cols = [c["name"] for c in result.get("cols", [])]
    return [dict(zip(cols, [cell.get("value") for cell in row])) for row in result.get("rows", [])]

def batch_update(ids, quality='size_mismatch'):
    """Batch UPDATE multiple product_matches in one pipeline call."""
    if not ids: return
    placeholders = ",".join(["?"] * len(ids))
    sql = f"UPDATE product_matches SET match_quality = ? WHERE id IN ({placeholders})"
    args = [quality] + ids
    execute(sql, args)

def main():
    # Reset all to ok first
    execute("UPDATE product_matches SET match_quality = 'ok'")
    
    matches = query("""
        SELECT pm.id, p1.name as iga_name, p1.price as iga_price, p1.size as iga_size,
               p2.name as tw_name, p2.price as tw_price, p2.size as tw_size
        FROM product_matches pm
        JOIN products p1 ON pm.iga_product_id = p1.id
        JOIN products p2 ON pm.thriftway_product_id = p2.id
        WHERE ABS(p1.price - p2.price) > 3
    """)
    
    print(f"Checking {len(matches)} matches with gap > $3...")
    
    multi_pack_patterns = [
        (r'(\d+)\s*Ea\b', 'ea'), (r'(\d+)\s*Pk\b', 'pack'),
        (r'(\d+)\s*Pack\b', 'pack'), (r'(\d+)\s*Ct\b', 'ct'),
        (r'Value\s*Pack', None), (r'Value\s*Size', None),
        (r'(\d+)\s*Can\b', 'can'),
    ]
    oz_pattern = re.compile(r'(\d+\.?\d*)\s*oz', re.IGNORECASE)
    
    category_conflicts = {
        'cream cheese': ['salmon', 'fish', 'lox'],
        'steak': ['stew', 'ground'],
        'ribeye': ['stew', 'ground'],
    }
    
    def extract_total_oz(name, size_field):
        text = f"{name} {size_field or ''}".lower()
        size_patterns = [
            (r'(\d+\.?\d*)\s*(fl\s*)?oz', 1), (r'(\d+\.?\d*)\s*lb', 16),
            (r'(\d+\.?\d*)\s*pound', 16), (r'(\d+\.?\d*)\s*gal', 128),
            (r'(\d+\.?\d*)\s*quart', 32), (r'(\d+\.?\d*)\s*pint', 16),
        ]
        best_oz = None
        for pattern, oz_per_unit in size_patterns:
            for match in re.finditer(pattern, text):
                total = float(match.group(1)) * oz_per_unit
                if best_oz is None or total > best_oz:
                    best_oz = total
        return best_oz
    
    flagged_ids = []
    for m in matches:
        mid = m['id']
        iga_name = str(m['iga_name'])
        tw_name = str(m['tw_name'])
        iga_price = float(m['iga_price'])
        tw_price = float(m['tw_price'])
        iga_size = str(m['iga_size'] or '')
        iga_lower, tw_lower = iga_name.lower(), tw_name.lower()
        price_ratio = max(iga_price, tw_price) / max(min(iga_price, tw_price), 0.01)
        
        reason = None
        
        # 1. Multi-pack detection
        for pattern, _ in multi_pack_patterns:
            match = re.search(pattern, iga_name, re.IGNORECASE)
            if match and match.groups():
                if int(match.group(1)) >= 4 and price_ratio > 2.0:
                    reason = f"multi-pack qty={match.group(1)}"
                    break
            elif match and not match.groups() and price_ratio > 2.0:
                reason = "value pack"
                break
        
        # 2. Spice jar vs per-lb
        if not reason and str(m['tw_size']) == 'per lb':
            has_oz = oz_pattern.search(iga_size) or oz_pattern.search(iga_name)
            if has_oz and float(has_oz.group(1)) <= 16 and tw_price > iga_price * 1.5:
                reason = f"jar-vs-per-lb"
        
        # 3. Category conflicts
        if not reason:
            for cat_term, exclude_terms in category_conflicts.items():
                if cat_term in tw_lower:
                    for ex_term in exclude_terms:
                        if ex_term in iga_lower and cat_term not in iga_lower:
                            reason = f"category: {ex_term} vs {cat_term}"
                            break
                    if reason: break
        
        # 4. Short IGA vs long TW
        if not reason and len(iga_lower.split()) <= 3 and len(tw_lower.split()) >= 6 and price_ratio > 5:
            reason = "short-vs-long name"
        
        # 5. Size ratio
        if not reason:
            iga_oz = extract_total_oz(iga_name, iga_size)
            tw_oz = extract_total_oz(tw_name, str(m['tw_size'] or ''))
            if iga_oz and tw_oz and min(iga_oz, tw_oz) > 0:
                if max(iga_oz, tw_oz) / min(iga_oz, tw_oz) >= 2.0:
                    reason = f"size ratio {max(iga_oz, tw_oz)/min(iga_oz, tw_oz):.1f}x"
        
        if reason:
            flagged_ids.append(mid)
            if len(flagged_ids) <= 10:
                print(f"  FLAGGED [{reason}]: {iga_name[:55]}")
    
    # Batch update all flagged IDs (single pipeline call)
    if flagged_ids:
        placeholders = ",".join(["?"] * len(flagged_ids))
        execute(f"UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id IN ({placeholders})", flagged_ids)
        print(f"\nBatch-updated {len(flagged_ids)} matches in one call")
    else:
        print("No matches flagged")
    
    final = query("SELECT match_quality, COUNT(*) as cnt FROM product_matches GROUP BY match_quality")
    for r in final:
        print(f"  {r['match_quality']}: {r['cnt']}")

if __name__ == "__main__":
    main()
