import sys
sys.path.insert(0, '.')
from db import query

# Match distribution
matches = query('SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type')
print('=== MATCH TYPES ===')
for m in matches:
    print(f"  {m['match_type']}: {m['cnt']}")

# Coverage
iga = query('''
    SELECT 
        (SELECT COUNT(*) FROM products WHERE store_id = 1) as total_iga,
        (SELECT COUNT(DISTINCT iga_product_id) FROM product_matches) as matched_iga
''')
tw = query('''
    SELECT 
        (SELECT COUNT(*) FROM products WHERE store_id = 2) as total_tw,
        (SELECT COUNT(DISTINCT tw_product_id) FROM product_matches) as matched_tw
''')
print(f"\n=== COVERAGE ===")
print(f"  IGA: {iga[0]['matched_iga']}/{iga[0]['total_iga']} ({iga[0]['matched_iga']/iga[0]['total_iga']*100:.1f}%)")
print(f"  Thriftway: {tw[0]['matched_tw']}/{tw[0]['total_tw']} ({tw[0]['matched_tw']/tw[0]['total_tw']*100:.1f}%)")

# Best matches by confidence
samples = query('''
    SELECT pm.match_type, pm.confidence, 
           p1.name as iga_name, p1.price_display as iga_price,
           p2.name as tw_name, p2.price_display as tw_price
    FROM product_matches pm
    JOIN products p1 ON pm.iga_product_id = p1.product_id
    JOIN products p2 ON pm.tw_product_id = p2.product_id
    ORDER BY pm.confidence DESC
    LIMIT 20
''')
print(f"\n=== TOP 20 MATCHES BY CONFIDENCE ===")
for s in samples:
    print(f"  [{s['match_type']} {s['confidence']:.2f}] {s['iga_name']} -> {s['tw_name']}")

# What does IGA product naming look like?
iga_samples = query('SELECT name, size, price_display FROM products WHERE store_id = 1 ORDER BY RANDOM() LIMIT 20')
print(f"\n=== RANDOM IGA PRODUCTS ===")
for s in iga_samples:
    print(f"  [{s['size']}] {s['name']} = {s['price_display']}")

# What does Thriftway naming look like?
tw_samples = query('SELECT name, size, price_display FROM products WHERE store_id = 2 ORDER BY RANDOM() LIMIT 20')
print(f"\n=== RANDOM THRIFTWAY PRODUCTS ===")
for s in tw_samples:
    print(f"  [{s['size']}] {s['name']} = {s['price_display']}")

# How many IGA products have UPC/barcodes?
barcodes = query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 1 AND barcode IS NOT NULL AND barcode != ""')
print(f"\n=== BARCODES ===")
print(f"  IGA with barcodes: {barcodes[0]['cnt']}")
tw_barcodes = query('SELECT COUNT(*) as cnt FROM products WHERE store_id = 2 AND barcode IS NOT NULL AND barcode != ""')
print(f"  Thriftway with barcodes: {tw_barcodes[0]['cnt']}")

# Look at actual IGA barcode format
bc_samples = query('SELECT name, barcode FROM products WHERE store_id = 1 AND barcode IS NOT NULL AND barcode != "" LIMIT 10')
print("  IGA barcode samples:")
for b in bc_samples:
    print(f"    {b['barcode']} -> {b['name']}")
