"""Full IGA scraper v2 — fixed DB args, per-department product scraping."""
import urllib.request, json, time, sys, os

sys.stdout.reconfigure(line_buffering=True)

APP_KEY = "vashon_fresh_market"
STORE_ID = "7432"
BASE = "https://api.freshop.ncrcloud.com"

# --- Turso creds & helpers ---
TOKEN = None
DB_URL = None
with open('/Users/johngoad/workspace/grocery-store-wars/scrapers/.env') as f:
    for line in f:
        line = line.strip()
        if 'TURSO_AUTH_TOKEN' in line:
            TOKEN = line.split('=',1)[1].strip('"').strip("'")
        if 'TURSO_DATABASE_URL' in line:
            raw = line.split('=',1)[1].strip('"').strip("'")
            if raw.startswith('libsql://'):
                parts = raw.replace('libsql://', '').split('.')
                org = parts[0].split('-')[-1]
                db = parts[0].replace(f'-{org}', '')
                DB_URL = f"https://{db}-{org}.aws-us-west-2.turso.io"

def wrap_arg(val):
    if val is None: return {"type": "null"}
    elif isinstance(val, bool): return {"type": "integer", "value": str(int(val))}
    elif isinstance(val, int): return {"type": "integer", "value": str(val)}
    elif isinstance(val, float): return {"type": "float", "value": val}
    else: return {"type": "text", "value": str(val)}

def db_execute(sql, params=None):
    wrapped = [wrap_arg(p) for p in (params or [])]
    body = {"requests": [{"type": "execute", "stmt": {"sql": sql, "args": wrapped}}]}
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{DB_URL}/v2/pipeline", data=data,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=15)

def api(path, **params):
    p = f"app_key={APP_KEY}"
    for k, v in params.items():
        p += f"&{k}={v}"
    url = f"{BASE}{path}?{p}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp

def insert_product(product):
    pid = str(product.get("id"))
    name = product.get("name", "")
    raw_price = product.get("price")
    unit_price = product.get("unit_price")
    if unit_price is None and raw_price is not None:
        try: unit_price = float(raw_price)
        except: pass
    upc = str(product.get("upc")) if product.get("upc") else None
    barcode = product.get("barcode") or product.get("barcode_upc_a")
    size = product.get("size")
    brand = product.get("brand")
    manufacturer = product.get("manufacturer")
    dept_ids = product.get("department_ids", [])
    dept_id = str(dept_ids[0]) if dept_ids else None
    images = product.get("images", [])
    img_url = None
    if images and images[0].get("identifier"):
        img_url = f"https://images.freshop.ncrcloud.com/{images[0]['identifier']}_medium.jpg"
    product_url = product.get("canonical_url")
    is_weight = 1 if product.get("is_weight_required") else 0
    qty_label = product.get("quantity_label")
    last_updated = product.get("last_updated_at")

    db_execute("""INSERT OR REPLACE INTO products (
        id, store_id, name, price, unit_price, price_display,
        upc, barcode, barcode_type, size, brand, manufacturer,
        department_id, image_url, product_url,
        is_weight_required, quantity_label, last_updated_at, is_iga
    ) VALUES (?,?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    [pid, "iga-vashon", name, unit_price, unit_price, str(raw_price) if isinstance(raw_price, str) else None,
     upc, barcode, "UPC-A", size, brand, manufacturer,
     dept_id, img_url, product_url,
     is_weight, qty_label, last_updated, 1])

    if unit_price is not None:
        try:
            db_execute(
                "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
                [pid, "iga-vashon", float(unit_price)])
        except: pass

# === MAIN ===
print("Loading departments...", flush=True)
all_depts = api("/1/departments", store_id=STORE_ID, no_limit="true")
departments = all_depts if isinstance(all_depts, list) else all_depts.get("items", [])
print(f"Got {len(departments)} departments", flush=True)

seen_products = set()
total_inserted = 0
start = time.time()

for i, dept in enumerate(departments):
    did = str(dept['id'])
    dname = dept.get('name', '?')
    
    try:
        data = api("/1/products", department_id=did, limit="100", offset="0")
        items = data if isinstance(data, list) else data.get("items", [])
        
        new_count = 0
        for item in items:
            if item['id'] not in seen_products:
                seen_products.add(item['id'])
                insert_product(item)
                new_count += 1
                total_inserted += 1
        
        if new_count > 0 or i % 100 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(departments) - i - 1) / rate if rate > 0 else 0
            print(f"[{i+1}/{len(departments)}] {dname[:30]}: {len(items)} items, {new_count} new | unique: {len(seen_products)} | {rate:.1f} dept/s | ETA: {eta:.0f}s", flush=True)
        
        time.sleep(0.3)
        
    except Exception as e:
        if i % 100 == 0:
            print(f"  Error on {dname}: {e}", flush=True)

# Update store metadata
db_execute(
    "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = 'iga-vashon'",
    [total_inserted]
)

elapsed = time.time() - start
print(f"\n=== DONE ===", flush=True)
print(f"Total unique products: {len(seen_products)}", flush=True)
print(f"Total inserted: {total_inserted}", flush=True)
print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f}m)", flush=True)
