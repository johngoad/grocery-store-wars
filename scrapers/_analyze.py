#!/usr/bin/env python3
"""Deep match analysis — understand where we are and what more we can do."""
import http.client, json, os, re

env_path = os.path.join(os.path.dirname(__file__), '.env')
token = None
if os.path.exists(env_path):
    for line in open(env_path):
        if line.startswith('TURSO_AUTH_TOKEN='):
            token = line.strip().split('=', 1)[1]
            break

host = 'grocery-store-wars-jg56789.aws-us-west-2.turso.io'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

def query(sql):
    conn = http.client.HTTPSConnection(host, timeout=30)
    body = json.dumps({'requests': [{'type': 'execute', 'stmt': sql}]})
    conn.request('POST', '/v2/pipeline', body, headers)
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    try:
        rows = data['results'][0]['response']['result']['rows']
        cols = [c['name'] for c in data['results'][0]['response']['result']['cols']]
        return [dict(zip(cols, [cell.get('value', str(cell)) for cell in row])) for row in rows]
    except Exception as e:
        return {'error': str(e), 'data': str(data)[:500]}

# 1. Current match distribution
print("=== MATCH TYPES ===")
for r in query('SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type'):
    print(f"  {r['match_type']}: {r['cnt']}")

# 2. Coverage
iga = query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 1')[0]['cnt']
tw = query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 2')[0]['cnt']
m_iga = query('SELECT COUNT(DISTINCT iga_product_id) as cnt FROM product_matches')[0]['cnt']
m_tw = query('SELECT COUNT(DISTINCT tw_product_id) as cnt FROM product_matches')[0]['cnt']
print(f"\n=== COVERAGE ===")
print(f"  IGA: {m_iga}/{iga} ({m_iga/iga*100:.1f}%)")
print(f"  Thriftway: {m_tw}/{tw} ({m_tw/tw*100:.1f}%)")

# 3. Top 20 matches
print(f"\n=== TOP 20 MATCHES ===")
for r in query('''SELECT pm.match_type, pm.confidence, 
    p1.name as iga_name, p2.name as tw_name
    FROM product_matches pm
    JOIN products p1 ON pm.iga_product_id = p1.product_id
    JOIN products p2 ON pm.tw_product_id = p2.product_id
    ORDER BY pm.confidence DESC LIMIT 20'''):
    print(f"  [{r['match_type']} {r['confidence']:.2f}] {r['iga_name']} -> {r['tw_name']}")

# 4. Random IGA products to understand naming
print(f"\n=== RANDOM IGA PRODUCTS ===")
for r in query('SELECT name, size, price_display FROM products WHERE store_id = 1 ORDER BY RANDOM() LIMIT 20'):
    print(f"  [{r['size']}] {r['name']} = {r['price_display']}")

# 5. Random Thriftway products
print(f"\n=== RANDOM THRIFTWAY PRODUCTS ===")
for r in query('SELECT name, size, price_display FROM products WHERE store_id = 2 ORDER BY RANDOM() LIMIT 20'):
    print(f"  [{r['size']}] {r['name']} = {r['price_display']}")

# 6. Barcode stats
print(f"\n=== BARCODES ===")
for r in query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 1 AND barcode IS NOT NULL AND barcode != ""'):
    print(f"  IGA with barcodes: {r['cnt']}")
for r in query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 2 AND barcode IS NOT NULL AND barcode != ""'):
    print(f"  Thriftway with barcodes: {r['cnt']}")

# 7. Top unmatched IGA categories — what are we missing?
print(f"\n=== UNMATCHED IGA — TOP DEPARTMENTS ===")
for r in query('''SELECT d.name as dept, COUNT(*) as cnt 
    FROM products p JOIN departments d ON p.department_id = d.department_id
    WHERE p.store_id = 1 AND p.product_id NOT IN (SELECT DISTINCT iga_product_id FROM product_matches)
    GROUP BY d.name ORDER BY cnt DESC LIMIT 15'''):
    print(f"  {r['dept']}: {r['cnt']}")

# 8. Size field differences
print(f"\n=== IGA SIZE FIELD ===")
for r in query('''SELECT size, COUNT(*) as cnt FROM products 
    WHERE store_id = 1 GROUP BY size ORDER BY cnt DESC LIMIT 10'''):
    print(f"  '{r['size']}': {r['cnt']}")
print(f"\n=== THRIFTWAY SIZE FIELD ===")
for r in query('''SELECT size, COUNT(*) as cnt FROM products 
    WHERE store_id = 2 GROUP BY size ORDER BY cnt DESC LIMIT 10'''):
    print(f"  '{r['size']}': {r['cnt']}")
