"""Deduplicate IGA price_history: keep only one row per (product_id, price) combo."""
import urllib.request, json, sys

sys.stdout.reconfigure(line_buffering=True)

# Load env
with open('/Users/johngoad/workspace/grocery-store-wars/scrapers/.env') as f:
    env_raw = f.read()

TOKEN = None
DB_URL = None
for line in env_raw.strip().split('\n'):
    if 'TURSO_AUTH_TOKEN' in line:
        TOKEN = line.split('=', 1)[1].strip('"').strip("'")
    if 'TURSO_DATABASE_URL' in line:
        raw = line.split('=', 1)[1].strip('"').strip("'")
        if raw.startswith('libsql://'):
            parts = raw.replace('libsql://', '').split('.')
            org = parts[0].split('-')[-1]
            db = parts[0].replace(f'-{org}', '')
            DB_URL = f"https://{db}-{org}.aws-west-us-2.turso.io"

def db_exec(sql):
    body = json.dumps({"requests": [{"type": "execute", "stmt": {"sql": sql}}]}).encode()
    req = urllib.request.Request(f"{DB_URL}/v2/pipeline", data=body,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return resp

def db_query(sql):
    r = db_exec(sql)
    rows = r['results'][0]['response']['result']['rows']
    return [row[0]['value'] for row in rows]

# Count before
before = db_query("SELECT COUNT(*) FROM price_history WHERE store_id='iga-vashon'")[0]
print(f"Before: {before} IGA price_history rows")

# Delete duplicates — keep one per (product_id, price) via MIN(rowid)
db_exec("""
DELETE FROM price_history 
WHERE store_id = 'iga-vashon'
AND rowid NOT IN (
    SELECT MIN(rowid) 
    FROM price_history 
    WHERE store_id = 'iga-vashon' 
    GROUP BY product_id, price
)
""")
print("Dedup executed")

after = db_query("SELECT COUNT(*) FROM price_history WHERE store_id='iga-vashon'")[0]
print(f"After: {after} IGA price_history rows")
print(f"Removed: {int(before) - int(after)} duplicate rows")

# Also collapse to one row per product (latest price) for real cleanliness
distinct_products = db_query("SELECT COUNT(DISTINCT product_id) FROM price_history WHERE store_id='iga-vashon'")[0]
print(f"Distinct products: {distinct_products}")
print("Done!")
