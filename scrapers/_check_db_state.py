"""Quick DB state check."""
import os, httpx

DB_URL = 'https://grocery-store-wars-jg56789.aws-us-west-2.turso.io'
# Load token from .env
token = ''
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if line.startswith('TURSO_AUTH_TOKEN='):
            token = line.strip().split('=', 1)[1]
            break

client = httpx.Client(
    base_url=DB_URL,
    headers={'Authorization': f'Bearer {token}'},
    timeout=30,
)

def run_sql(sql):
    r = client.post('/v2/pipeline', json={'requests': [
        {'type': 'execute', 'stmt': {'sql': sql}}
    ]})
    data = r.json()
    return data['results'][0]['response']['result']

queries = [
    ('STORES', 'SELECT * FROM stores'),
    ('PRODUCTS BY STORE', 'SELECT store_id, COUNT(*) as cnt FROM products GROUP BY store_id'),
    ('MATCHES', 'SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type'),
    ('TOTAL MATCHES', 'SELECT COUNT(*) as cnt FROM product_matches'),
    ('STAPLES', 'SELECT COUNT(*) as cnt FROM staple_items'),
    ('PRICE HISTORY', 'SELECT store_id, COUNT(*) as cnt FROM price_history GROUP BY store_id'),
]

for label, sql in queries:
    result = run_sql(sql)
    rows = result.get('rows', [])
    print(f'{label}: {rows}')
