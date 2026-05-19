#!/usr/bin/env python3
"""Deep match analysis with better error handling."""
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
    body = json.dumps({'requests': [{'type': 'execute', 'stmt': sql}]})
    conn.request('POST', '/v2/pipeline', body, headers)
    resp = conn.getresponse()
    raw = resp.read()
    conn.close()
    data = json.loads(raw)
    if 'error' in data:
        return {'_error': data['error']}
    try:
        result = data['results'][0]
        if 'error' in result:
            return {'_error': result['error']}
        rows = result['response']['result']['rows']
        cols = [c['name'] for c in result['response']['result']['cols']]
        return [dict(zip(cols, [cell.get('value', str(cell)) for cell in row])) for row in rows]
    except Exception as e:
        return {'_error': str(e), '_raw': str(data)[:300]}

def one(sql):
    r = query(sql)
    if isinstance(r, dict) and '_error' in r:
        print(f"  ERROR: {r}")
        return '?'
    return r[0] if r else {}

def run(*sqls):
    for sql in sqls:
        r = query(sql)
        if isinstance(r, dict) and '_error' in r:
            print(f"  ERROR: {r['_error']}")
        else:
            for row in r:
                print(f"  {row}")

# Quick test
r = query('SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type')
print("Raw result:", json.dumps(r, indent=2, default=str)[:600])
