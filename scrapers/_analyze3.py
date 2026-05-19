#!/usr/bin/env python3
"""Query Turso DB using the working format from check_db.py."""
import http.client, json, os

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
    body = json.dumps({'type': 'execute', 'stmt': sql})
    conn.request('POST', '/v2/pipeline', body, headers)
    resp = conn.getresponse()
    raw = resp.read()
    conn.close()
    data = json.loads(raw)
    if 'error' in data:
        return {'_error': data['error']}
    try:
        rows = data['results'][0]['response']['result']['rows']
        return rows
    except Exception as e:
        return {'_error': str(e), '_raw': str(data)[:300]}

# Quick test
r = query('SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type')
print("Match types:", json.dumps(r, indent=2, default=str)[:800])

r = query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 1')
print("\nIGA total:", r[0][0]['value'] if r else '?')

r = query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 2')
print("TW total:", r[0][0]['value'] if r else '?')

r = query('SELECT COUNT(DISTINCT iga_product_id) as cnt FROM product_matches')
print("Matched IGA:", r[0][0]['value'] if r else '?')

r = query('SELECT COUNT(*) as cnt FROM product_matches')
print("Total matches:", r[0][0]['value'] if r else '?')

# Sample IGA product names
r = query('SELECT name, size FROM products WHERE store_id = 1 LIMIT 10')
print("\nIGA samples:")
for row in r:
    print(f"  {row[0]['value']} | {row[1].get('value', '')}")

# Sample TW product names
r = query('SELECT name, size FROM products WHERE store_id = 2 LIMIT 10')
print("\nTW samples:")
for row in r:
    print(f"  {row[0]['value']} | {row[1].get('value', '')}")

# What departments have most unmatched IGA products?
r = query('''SELECT d.name, COUNT(*) as cnt FROM products p 
    JOIN departments d ON p.department_id = d.department_id
    WHERE p.store_id = 1 AND p.product_id NOT IN (SELECT DISTINCT iga_product_id FROM product_matches)
    GROUP BY d.name ORDER BY cnt DESC LIMIT 10''')
print("\nTop unmatched IGA departments:")
for row in r:
    print(f"  {row[0]['value']}: {row[1]['value']}")

# Best matches
r = query('''SELECT pm.confidence, p1.name as n1, p2.name as n2
    FROM product_matches pm
    JOIN products p1 ON pm.iga_product_id = p1.product_id
    JOIN products p2 ON pm.tw_product_id = p2.product_id
    ORDER BY pm.confidence DESC LIMIT 10''')
print("\nTop matches:")
for row in r:
    print(f"  {row[0]['value']:.2f}: {row[1]['value']} -> {row[2]['value']}")
