#!/usr/bin/env python3
"""Check Turso DB row counts and stats."""
import http.client, json, os

# Read token from .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
token = None
if os.path.exists(env_path):
    for line in open(env_path):
        if line.startswith('TURSO_AUTH_TOKEN='):
            token = line.strip().split('=', 1)[1]
            break
if not token:
    print("ERROR: TURSO_AUTH_TOKEN not found in .env")
    exit(1)

conn = http.client.HTTPSConnection('grocery-store-wars-jg56789.aws-us-west-2.turso.io', timeout=15)
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

def count(table):
    body = json.dumps({'type': 'execute', 'stmt': f'SELECT count(*) as cnt FROM {table}'})
    conn.request('POST', '/v2/pipeline', body, headers)
    resp = conn.getresponse()
    data = json.loads(resp.read())
    try:
        return data['results'][0]['response']['result']['rows'][0][0]['value']
    except Exception:
        return f'ERROR: {data}'

tables = ['stores', 'products', 'price_history', 'departments', 'product_matches', 'staple_items']
print("TABLE              COUNT")
print("-----              -----")
for table in tables:
    cnt = count(table)
    print(f'{table:<20} {cnt}')

conn.close()
