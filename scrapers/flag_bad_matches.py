#!/usr/bin/env python3
"""Flag poor-quality product_matches for dashboard filtering.
Detects: multi-pack vs single, spice jar vs per-lb, category conflicts, short-name mismatches.
Run after any matcher re-run to clean the results.
"""
import re, os, httpx
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
    return resp.json()["results"][0]["response"]["result"]

def query(sql, params=None):
    result = execute(sql, params)
    if not result or "rows" not in result: return []
    cols = [c["name"] for c in result.get("cols", [])]
    return [dict(zip(cols, [cell.get("value") for cell in row])) for row in result.get("rows", [])]

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
    
    # --- Size extraction helpers ---
    def extract_total_oz(name, size_field):
        text = f"{name} {size_field or ''}".lower()
        size_patterns = [
            (r'(\d+\.?\d*)\s*(fl\s*)?oz', 1),
            (r'(\d+\.?\d*)\s*lb', 16),
            (r'(\d+\.?\d*)\s*pound', 16),
            (r'(\d+\.?\d*)\s*gal', 128),
            (r'(\d+\.?\d*)\s*quart', 32),
            (r'(\d+\.?\d*)\s*pint', 16),
        ]
        best_oz = None
        for pattern, oz_per_unit in size_patterns:
            for match in re.finditer(pattern, text):
                total = float(match.group(1)) * oz_per_unit
                if best_oz is None or total > best_oz:
                    best_oz = total
        return best_oz
    
    flagged = 0
    for m in matches:
        mid, iga_name, iga_price = m['id'], str(m['iga_name']), float(m['iga_price'])
        tw_name, tw_price = str(m['tw_name']), float(m['tw_price'])
        iga_size = str(m['iga_size'] or '')
        iga_lower, tw_lower = iga_name.lower(), tw_name.lower()
        price_ratio = max(iga_price, tw_price) / max(min(iga_price, tw_price), 0.01)
        
        # 1. Multi-pack detection
        for pattern, _ in multi_pack_patterns:
            match = re.search(pattern, iga_name, re.IGNORECASE)
            if match and match.groups():
                qty = int(match.group(1))
                if qty >= 4 and price_ratio > 2.0:
                    execute("UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id = ?", [mid])
                    flagged += 1
                    break
            elif match and not match.groups() and price_ratio > 3:
                execute("UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id = ?", [mid])
                flagged += 1
                break
        
        # 2. Spice jar vs per-lb
        if str(m['tw_size']) == 'per lb':
            has_oz = oz_pattern.search(iga_size) or oz_pattern.search(iga_name)
            if has_oz and float(has_oz.group(1)) <= 16 and tw_price > iga_price * 3:
                execute("UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id = ?", [mid])
                flagged += 1
        
        # 3. Category conflicts
        for cat_term, exclude_terms in category_conflicts.items():
            if cat_term in tw_lower:
                for ex_term in exclude_terms:
                    if ex_term in iga_lower and cat_term not in iga_lower:
                        execute("UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id = ?", [mid])
                        flagged += 1
                        break
        
        # 4. Short IGA matched to long Thriftway + huge gap
        iga_words = len(iga_lower.split())
        tw_words = len(tw_lower.split())
        if iga_words <= 3 and tw_words >= 6 and price_ratio > 5:
            execute("UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id = ?", [mid])
            flagged += 1
        
        # 5. Extractable size mismatch — same product, different package sizes
        iga_oz = extract_total_oz(iga_name, iga_size)
        tw_oz = extract_total_oz(tw_name, str(m['tw_size'] or ''))
        if iga_oz and tw_oz and min(iga_oz, tw_oz) > 0:
            size_ratio = max(iga_oz, tw_oz) / min(iga_oz, tw_oz)
            if size_ratio >= 2.0:
                execute("UPDATE product_matches SET match_quality = 'size_mismatch' WHERE id = ?", [mid])
                flagged += 1
    
    final = query("SELECT match_quality, COUNT(*) as cnt FROM product_matches GROUP BY match_quality")
    for r in final:
        print(f"  {r['match_quality']}: {r['cnt']}")
    print(f"Flagged {flagged} total")

if __name__ == "__main__":
    main()
