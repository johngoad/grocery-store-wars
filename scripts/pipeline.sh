#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

LOG="logs/pipeline-$(date +%Y%m%d-%H%M).log"
mkdir -p logs
exec > >(tee -a "$LOG") 2>&1

echo "=== GSW Pipeline: $(date) ==="

# 1. Refresh Turso token
echo "[1/6] Refreshing Turso token..."
cd scrapers
source .venv/bin/activate
turso db tokens create grocery-store-wars > /tmp/turso_token_pipeline.txt
TOKEN=$(cat /tmp/turso_token_pipeline.txt)
sed -i '' "s|TURSO_AUTH_TOKEN=.*|TURSO_AUTH_TOKEN=$TOKEN|" .env
echo "  Token refreshed (${#TOKEN} chars)"

# 2. Scrape IGA
echo "[2/6] Scraping IGA Vashon..."
python full_iga_v2.py
echo "  IGA scrape complete"

# 3. Scrape Thriftway
echo "[3/6] Scraping Thriftway Vashon..."
python run_mercato.py
echo "  Thriftway scrape complete"

# 4. Extract sizes
echo "[4/6] Extracting Thriftway sizes..."
python extract_sizes.py
echo "  Size extraction complete"

# 5. Match products
echo "[5/6] Matching products..."
python run_matcher_v4.py
echo "  Matching complete"

# 6. Flag bad matches
echo "[6/6] Flagging bad matches..."
python flag_bad_matches.py
echo "  Flagging complete"

# 7. Verify data
echo "=== Verification ==="
turso db shell grocery-store-wars "SELECT 'IGA: ' || COUNT(*) FROM products WHERE store_id='iga-vashon'; SELECT 'TW: ' || COUNT(*) FROM products WHERE store_id='thriftway-vashon'; SELECT 'Matches: ' || COUNT(*) FROM product_matches; SELECT 'Size mismatch: ' || COUNT(*) FROM product_matches WHERE match_quality='size_mismatch'; SELECT 'TW size_oz: ' || COUNT(*) FROM products WHERE store_id='thriftway-vashon' AND size_oz IS NOT NULL;"

# 8. Commit and push
echo "=== Git commit ==="
cd "$(dirname "$0")/.."
git add -A
git commit -m "auto: daily pipeline run $(date +%Y-%m-%d)" || echo "  Nothing to commit"
git push origin main || echo "  Push failed (non-fatal)"

echo "=== Pipeline complete: $(date) ==="
echo "Log: $LOG"
