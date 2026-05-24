"""Extract real sizes from Thriftway product names and update size_oz column.
Mercato API returns size='each' for 90% of products. Actual sizes are in the names.
Handles: Fluid Ounces, Ounces, Pounds, Grams, Milliliters, multi-packs, fractions.
"""
import re, os, json
import httpx
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://")
DB_TOKEN = os.environ["TURSO_AUTH_TOKEN"]

client = httpx.Client(base_url=DB_URL, headers={"Authorization": f"Bearer {DB_TOKEN}"}, timeout=60)

def pipeline(requests):
    resp = client.post("/v2/pipeline", json={"requests": requests})
    resp.raise_for_status()
    data = resp.json()
    results = []
    for r in data.get("results", []):
        if r["type"] == "ok": results.append(r["response"])
        elif r["type"] == "error": raise Exception(f"Turso error: {r['error']}")
    return results

def query(sql):
    resp = client.post("/v2/pipeline", json={"requests": [{"type": "execute", "stmt": {"sql": sql}}]})
    data = resp.json()
    exec_result = data["results"][0]["response"]["result"]
    columns = [col["name"] for col in exec_result.get("cols", [])]
    rows = []
    for row in exec_result.get("rows", []):
        values = []
        for cell in row:
            val = cell.get("value")
            if cell.get("type") in ("integer",):
                try: val = int(val)
                except: pass
            elif cell.get("type") in ("float",):
                try: val = float(val)
                except: pass
            values.append(val)
        rows.append(dict(zip(columns, values)))
    return rows

def batch_execute(statements):
    requests = []
    for sql, params in statements:
        args = []
        if params:
            for p in params:
                if p is None: args.append({"type": "null"})
                elif isinstance(p, int): args.append({"type": "integer", "value": str(p)})
                elif isinstance(p, float): args.append({"type": "float", "value": p})
                else: args.append({"type": "text", "value": str(p)})
        requests.append({"type": "execute", "stmt": {"sql": sql, "args": args} if args else {"sql": sql}})
    return pipeline(requests)

COUNT_TERMS = r'\b(count|ct|pair|pairs|bag|bags|capsule|capsules|tablet|tablets|patch|patches|skewer|skewers|sheet|sheets|pack|packs|roll|rolls|toaster pastry|toaster pastries|bar|bars)\b'

def extract_total_oz(name, size_field):
    text = f"{name} {size_field or ''}".lower()
    if re.search(COUNT_TERMS, text): return None
    multipack = re.search(r'(\d+)\s*x\s*(\d+\.?\d*)\s*(fl\.?\s*)?(oz|ounce|fluid ounce)', text)
    if multipack: return float(multipack.group(1)) * float(multipack.group(2))
    frac = re.search(r'(\d+)\s*/\s*(\d+)\s*(lb|pound)', text)
    if frac: return (float(frac.group(1)) / float(frac.group(2))) * 16
    size_patterns = [
        (r'(\d+\.?\d*)\s*fluid\s*ounce', 1), (r'(\d+\.?\d*)\s*ounce', 1),
        (r'(\d+\.?\d*)\s*pound', 16), (r'(\d+\.?\d*)\s*fl\.?\s*oz', 1),
        (r'(?<!\w)(\d+\.?\d*)\s*oz\b', 1), (r'(\d+\.?\d*)\s*lb', 16),
        (r'(\d+\.?\d*)\s*gal', 128), (r'(\d+\.?\d*)\s*quart', 32),
        (r'(\d+\.?\d*)\s*pint', 16), (r'(\d+\.?\d*)\s*ml\b', lambda v: v / 29.5735),
        (r'(\d+\.?\d*)\s*milliliter', lambda v: v / 29.5735),
        (r'(\d+\.?\d*)\s*gram', lambda v: v / 28.3495),
        (r'(\d+\.?\d*)\s*liter', lambda v: v * 33.814),
    ]
    best_oz = None
    for pattern, converter in size_patterns:
        for match in re.finditer(pattern, text):
            val = float(match.group(1))
            oz = converter(val) if callable(converter) else val * converter
            if best_oz is None or oz > best_oz: best_oz = oz
    return best_oz

def extract_size_string(name, size_field):
    text = f"{name} {size_field or ''}".lower()
    if re.search(COUNT_TERMS, text): return None
    patterns = [
        (r'(\d+\.?\d*)\s*fluid\s*ounce', 'fl oz'), (r'(\d+\.?\d*)\s*ounce', 'oz'),
        (r'(\d+\.?\d*)\s*pound', 'lb'), (r'(\d+\.?\d*)\s*fl\.?\s*oz', 'fl oz'),
        (r'(?<!\w)(\d+\.?\d*)\s*oz\b', 'oz'), (r'(\d+\.?\d*)\s*lb', 'lb'),
        (r'(\d+\.?\d*)\s*gal', 'gal'), (r'(\d+\.?\d*)\s*quart', 'qt'),
        (r'(\d+\.?\d*)\s*pint', 'pt'), (r'(\d+\.?\d*)\s*ml\b', 'ml'),
        (r'(\d+\.?\d*)\s*milliliter', 'ml'), (r'(\d+\.?\d*)\s*gram', 'g'),
        (r'(\d+\.?\d*)\s*liter', 'l'),
    ]
    best, best_val = None, 0
    for pattern, unit in patterns:
        for match in re.finditer(pattern, text):
            val = float(match.group(1))
            if val > best_val: best_val = val; best = f"{match.group(1)} {unit}"
    return best

def main():
    print("=== Thriftway Size Extractor ===")
    count = query("SELECT COUNT(*) as cnt FROM products WHERE store_id='thriftway-vashon' AND (size_oz IS NULL OR size='each' OR size='per lb')")
    total = count[0]['cnt']
    print(f"Products needing extraction: {total}")
    
    products = query("SELECT id, name, size FROM products WHERE store_id='thriftway-vashon' AND (size_oz IS NULL OR size='each' OR size='per lb')")
    updates = []
    for p in products:
        oz = extract_total_oz(p['name'], p['size'])
        size_str = extract_size_string(p['name'], p['size'])
        if oz is not None: updates.append((p['id'], oz, size_str))
    print(f"Extracted sizes for {len(updates)}/{len(products)} products ({round(len(updates)/len(products)*100, 1)}%)")
    
    # Also fix per-lb items: size_oz = 16
    per_lb = query("SELECT COUNT(*) as cnt FROM products WHERE store_id='thriftway-vashon' AND size='per lb' AND size_oz IS NULL")
    print(f"Per-lb items missing size_oz: {per_lb[0]['cnt']}")
    
    # Batch update sizes
    CHUNK = 50
    total_updated = 0
    for i in range(0, len(updates), CHUNK):
        chunk = updates[i:i+CHUNK]
        stmts = [(f"UPDATE products SET size_oz = ?, size = ? WHERE id = ?", [oz, size_str or 'each', pid]) for pid, oz, size_str in chunk]
        batch_execute(stmts)
        total_updated += len(chunk)
        if (i // CHUNK) % 20 == 0: print(f"  {total_updated}/{len(updates)}...")
    
    # Fix per-lb
    if per_lb[0]['cnt'] > 0:
        batch_execute([("UPDATE products SET size_oz = 16 WHERE store_id='thriftway-vashon' AND size='per lb' AND size_oz IS NULL", [])])
        total_updated += per_lb[0]['cnt']
    
    # Verify
    verify = query("SELECT COUNT(*) as total, COUNT(CASE WHEN size_oz IS NOT NULL THEN 1 END) as has_oz FROM products WHERE store_id='thriftway-vashon'")
    v = verify[0]
    print(f"\nFinal coverage: {v['has_oz']}/{v['total']} ({round(v['has_oz']/v['total']*100, 1)}%)")
    print("Done.")

if __name__ == "__main__":
    main()
