"""Mercato price scraper for Thriftway — saves to Turso DB."""
import time, random, asyncio, os, json, urllib.request
from playwright.async_api import async_playwright

MERCATO_BASE = "https://www.mercato.com/shop/vashon-thriftway"
STORE_ID = "thriftway-vashon"

# --- DB helpers ---
TOKEN = None
DB_URL = None
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path) as f:
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
            else:
                DB_URL = raw

def db_execute(sql, params=None):
    body = {"requests": [{"type": "execute", "stmt": {"sql": sql, "args": params or []}}]}
    req = urllib.request.Request(
        f"{DB_URL}/v2/pipeline",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=15)

def save_product(name, price_str, query_term):
    """Save a product from Mercato search results."""
    import hashlib
    pid = f"mercato-{hashlib.md5(name.encode()).hexdigest()[:16]}"
    
    # Parse price
    price = None
    if price_str:
        import re
        nums = re.findall(r'[\d.]+', price_str.replace('$',''))
        if nums:
            price = float(nums[0])
    
    db_execute("""INSERT OR REPLACE INTO products (
        id, store_id, name, price, price_display, last_updated_at
    ) VALUES (?, ?, ?, ?, ?, datetime('now'))""",
        [pid, STORE_ID, name[:200], price, price_str]
    )
    
    if price:
        db_execute(
            "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
            [pid, STORE_ID, price]
        )
    
    return pid

STAPLE_SEARCHES = [
    "milk whole gallon", "eggs large dozen", "ground beef 80/20",
    "mayonnaise hellmann", "bread sourdough", "butter unsalted",
    "chicken breast", "cheese cheddar", "yogurt greek",
    "coffee ground", "bananas", "lettuce romaine",
    "tomatoes", "potatoes russet", "onions yellow",
    "orange juice", "bacon", "sausage", "lunch meat turkey",
    "cereal cheerios", "pasta spaghetti", "rice white",
    "canned tuna", "peanut butter", "jelly grape",
    "chips potato", "soda cola", "water bottled",
    "paper towels", "toilet paper", "dish soap",
    "laundry detergent", "flour all-purpose", "sugar white",
    "oil olive",
]

async def human_delay(min_s=3, max_s=8):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def scrape_staples():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()
        
        await page.goto(MERCATO_BASE, wait_until="networkidle", timeout=30000)
        await human_delay(4, 7)
        
        for i, query in enumerate(STAPLE_SEARCHES):
            try:
                # Find search box
                search_box = None
                for sel in ['input[type="search"]', 'input[placeholder*="Search"]', 'input[placeholder*="search"]']:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=2000):
                        search_box = el
                        break
                
                if not search_box:
                    print(f"  [{i+1}/{len(STAPLE_SEARCHES)}] No search box for '{query}'")
                    continue
                
                await search_box.click()
                await search_box.fill("")
                await asyncio.sleep(0.5)
                await search_box.fill(query)
                await page.keyboard.press("Enter")
                await human_delay(4, 8)
                
                # Extract results
                products = await page.evaluate("""() => {
                    const items = [];
                    document.querySelectorAll('[data-testid="product-card"], .product-card, [class*="product"]').forEach(card => {
                        const name = card.querySelector('h3, h4, [class*="name"], [class*="title"]')?.textContent?.trim();
                        const price = card.querySelector('[class*="price"], [data-testid="product-price"]')?.textContent?.trim();
                        if (name && price) items.push({name, price});
                    });
                    return items.slice(0, 5);
                }""")
                
                if products:
                    pid = save_product(products[0]['name'], products[0]['price'], query)
                    results.append({"query": query, "name": products[0]['name'], "price": products[0]['price']})
                    print(f"  [{i+1}/{len(STAPLE_SEARCHES)}] '{query}' -> {products[0]['name'][:50]} @ {products[0]['price']}")
                else:
                    print(f"  [{i+1}/{len(STAPLE_SEARCHES)}] '{query}' -> no results")
                
                await page.goto(MERCATO_BASE, wait_until="networkidle", timeout=30000)
                await human_delay(3, 6)
                
            except Exception as e:
                print(f"  [{i+1}/{len(STAPLE_SEARCHES)}] Error on '{query}': {e}")
                try:
                    await page.goto(MERCATO_BASE, wait_until="networkidle", timeout=30000)
                    await human_delay(3, 6)
                except:
                    pass
        
        await browser.close()
    
    # Update store
    saved = len([r for r in results if r.get('name')])
    db_execute(
        "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = ?",
        [saved, STORE_ID]
    )
    
    return results

async def main():
    print(f"Mercato Thriftway scraper — {len(STAPLE_SEARCHES)} staples\n")
    results = await scrape_staples()
    saved = len([r for r in results if r.get('name')])
    print(f"\nDone: {saved}/{len(STAPLE_SEARCHES)} items saved to DB")
    return results

if __name__ == "__main__":
    asyncio.run(main())
