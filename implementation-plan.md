# Grocery Store Wars — Implementation Plan (MVP)

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a competitive intelligence dashboard where the IGA owner sees their prices vs Thriftway side-by-side, searches products, scans barcodes, and finds margin opportunities.

**Architecture:** Monorepo — Next.js 15 (App Router) frontend on Vercel, Python FastAPI scrapers on a single $0 VPS or scheduled via GitHub Actions. Turso (SQLite-compatible) for cloud DB. Both stores' product data from Freshop API (IGA live, Thriftway catalog-only). Thriftway prices scraped carefully from Mercato for top 200 staple items only; long-tail uses stale Freshop prices flagged as unverified.

**Tech Stack:** Next.js 15, Tailwind CSS, shadcn/ui, Recharts, Turso (SQLite), NextAuth.js, FastAPI (Python), Playwright (replaces Puppeteer — lighter), ZXing (barcode fallback)

**Constraints:** Zero monthly spend. No residential proxies. Cloud hosted on free tiers. IGA owner enters their prices manually. MVP ships in 4 weeks.

---

## PHASE 0: Project Scaffold (Day 1)

### Task 0.1: Create monorepo structure

**Objective:** Initialize the grocery-store-wars monorepo with frontend and scraper directories

**Files:**
- Create: `grocery-store-wars/package.json`
- Create: `grocery-store-wars/frontend/` (Next.js)
- Create: `grocery-store-wars/scrapers/` (Python)

**Step 1: Create root directory and git init**

```bash
cd /Users/johngoad/workspace/grocery-store-wars
git init
```

**Step 2: Create root package.json**

```bash
cat > package.json << 'EOF'
{
  "name": "grocery-store-wars",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "cd frontend && npm run dev",
    "build": "cd frontend && npm run build",
    "scrape:iga": "cd scrapers && python -m scrapers.iga",
    "scrape:thriftway": "cd scrapers && python -m scrapers.thriftway",
    "match": "cd scrapers && python -m scrapers.matcher"
  }
}
EOF
```

**Step 3: Create basic README**

```bash
cat > README.md << 'EOF'
# Grocery Store Wars

Competitive pricing intelligence for independent grocers.
Compare your prices against the competition and find margin opportunities.

Built for IGA Vashon Market Fresh vs Vashon Thriftway.
White-labeled for resale to any independent grocer.
EOF
```

**Verification:** `ls -la` shows package.json, README.md. `git status` shows clean new repo.

---

### Task 0.2: Scaffold Next.js frontend

**Objective:** Create Next.js 15 App Router project with Tailwind and shadcn/ui

**Files:**
- Create: `frontend/` (full Next.js project)

**Step 1: Create Next.js app**

```bash
cd /Users/johngoad/workspace/grocery-store-wars
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack
cd frontend
```

**Step 2: Install core dependencies**

```bash
npm install next-auth@beta @auth/prisma-adapter @libsql/client recharts lucide-react
npm install -D @types/node
```

**Step 3: Initialize shadcn/ui**

```bash
npx shadcn@latest init -d
npx shadcn@latest add button card input table tabs select dialog dropdown-menu sheet badge separator skeleton tooltip avatar
```

**Step 4: Verify dev server starts**

```bash
npm run dev
# Visit http://localhost:3000 — should see Next.js welcome page
# Kill server with Ctrl+C
```

**Verification:** `npm run dev` starts without errors. `http://localhost:3000` renders.

---

### Task 0.3: Scaffold Python scraper project

**Objective:** Create Python project with FastAPI, requests, and Playwright

**Files:**
- Create: `scrapers/pyproject.toml`
- Create: `scrapers/scrapers/__init__.py`
- Create: `scrapers/scrapers/iga.py`
- Create: `scrapers/scrapers/thriftway.py`
- Create: `scrapers/scrapers/matcher.py`
- Create: `scrapers/scrapers/db.py`

**Step 1: Create pyproject.toml**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
cat > pyproject.toml << 'EOF'
[project]
name = "grocery-store-wars-scrapers"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "httpx>=0.27",
    "python-dotenv>=1.0",
    "libsql-client>=0.3",
    "playwright>=1.44",
    "thefuzz>=0.22",
    "python-Levenshtein>=0.25",
    "fastapi>=0.111",
    "uvicorn>=0.30",
]

[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
EOF
```

**Step 2: Create virtual environment and install**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

**Step 3: Create placeholder module files**

```bash
mkdir -p scrapers
touch scrapers/__init__.py
touch scrapers/iga.py
touch scrapers/thriftway.py
touch scrapers/matcher.py
touch scrapers/db.py
echo "print('Scrapers package ready')" > scrapers/__init__.py
python -c "import scrapers; print('OK')"
```

**Verification:** `python -c "import scrapers"` prints "Scrapers package ready". `playwright` command available.

---

### Task 0.4: Set up Turso database

**Objective:** Create Turso database and get connection credentials

**Files:**
- Create: `frontend/.env.local`
- Create: `scrapers/.env`

**Step 1: Install Turso CLI**

```bash
# macOS
brew install tursodatabase/tap/turso
# Or: curl -sSfL https://get.tur.so/install.sh | bash
```

**Step 2: Sign up / login**

```bash
turso auth signup
# Follow browser prompt to create account
```

**Step 3: Create database**

```bash
turso db create grocery-store-wars
# Note the database URL output
```

**Step 4: Get auth token**

```bash
turso db tokens create grocery-store-wars
# Save this token — it won't be shown again
```

**Step 5: Create .env files**

```bash
# frontend/.env.local
cat > /Users/johngoad/workspace/grocery-store-wars/frontend/.env.local << 'EOF'
TURSO_DATABASE_URL=libsql://grocery-store-wars-[your-org].turso.io
TURSO_AUTH_TOKEN=[token-from-step-4]
NEXTAUTH_SECRET=$(openssl rand -base64 32)
NEXTAUTH_URL=http://localhost:3000
EOF

# scrapers/.env
cat > /Users/johngoad/workspace/grocery-store-wars/scrapers/.env << 'EOF'
TURSO_DATABASE_URL=libsql://grocery-store-wars-[your-org].turso.io
TURSO_AUTH_TOKEN=[token-from-step-4]
EOF
```

**Step 6: Test connection**

```bash
turso db shell grocery-store-wars "SELECT 1;"
# Should print: 1
```

**Verification:** `turso db shell` connects and runs SQL. Both .env files exist with real credentials.

---

## PHASE 1: Database Layer (Day 1-2)

### Task 1.1: Create database schema migration

**Objective:** Write SQL schema matching the blueprint and apply it to Turso

**Files:**
- Create: `frontend/src/db/schema.sql`
- Create: `frontend/src/db/index.ts`

**Step 1: Write schema SQL**

Create `frontend/src/db/schema.sql`:

```sql
-- Stores
CREATE TABLE IF NOT EXISTS stores (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    store_id TEXT,
    base_url TEXT,
    last_scraped_at TEXT,
    product_count INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1
);

-- Departments
CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL REFERENCES stores(id),
    name TEXT NOT NULL,
    parent_id TEXT,
    product_count INTEGER DEFAULT 0
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL REFERENCES stores(id),
    name TEXT NOT NULL,
    price REAL,
    unit_price REAL,
    price_display TEXT,
    upc TEXT,
    barcode TEXT,
    barcode_type TEXT,
    size TEXT,
    brand TEXT,
    manufacturer TEXT,
    department_id TEXT,
    category TEXT,
    image_url TEXT,
    product_url TEXT,
    is_weight_required INTEGER DEFAULT 0,
    quantity_label TEXT,
    last_updated_at TEXT,
    scraped_at TEXT DEFAULT (datetime('now')),
    is_iga INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_products_store ON products(store_id);
CREATE INDEX IF NOT EXISTS idx_products_upc ON products(upc);
CREATE INDEX IF NOT EXISTS idx_products_department ON products(department_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- Price History
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(id),
    store_id TEXT NOT NULL REFERENCES stores(id),
    price REAL NOT NULL,
    recorded_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at);

-- Product Matches
CREATE TABLE IF NOT EXISTS product_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iga_product_id TEXT NOT NULL REFERENCES products(id),
    thriftway_product_id TEXT NOT NULL REFERENCES products(id),
    match_type TEXT NOT NULL DEFAULT 'fuzzy_name',
    confidence REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_matches_iga ON product_matches(iga_product_id);

-- Staple Items (KPI dashboard)
CREATE TABLE IF NOT EXISTS staple_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    iga_product_id TEXT REFERENCES products(id),
    thriftway_product_id TEXT REFERENCES products(id),
    category TEXT,
    display_order INTEGER DEFAULT 0
);

-- Users (for auth)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Scan History
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upc TEXT,
    product_name TEXT,
    iga_price REAL,
    thriftway_price REAL,
    scanned_at TEXT DEFAULT (datetime('now'))
);
```

**Step 2: Apply schema to Turso**

```bash
turso db shell grocery-store-wars < /Users/johngoad/workspace/grocery-store-wars/frontend/src/db/schema.sql
```

**Step 3: Create DB client module**

Create `frontend/src/db/index.ts`:

```typescript
import { createClient } from "@libsql/client";

const turso = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

export { turso };
export default turso;
```

**Step 4: Seed store records**

```bash
turso db shell grocery-store-wars << 'SQL'
INSERT INTO stores (id, name, platform, store_id, base_url) VALUES
  ('iga-vashon', 'IGA Vashon Market Fresh', 'freshop', '7432', 'https://shop.vashonmarket.com'),
  ('thriftway-vashon', 'Vashon Thriftway', 'freshop', '1813', 'https://www.vashonthriftway.com');
SQL
```

**Verification:** `turso db shell grocery-store-wars ".tables"` shows all 8 tables. `turso db shell grocery-store-wars "SELECT * FROM stores;"` returns 2 rows.

---

### Task 1.2: Create Python DB module for scrapers

**Objective:** Python can read/write to Turso

**Files:**
- Modify: `scrapers/scrapers/db.py`

**Step 1: Write db.py**

```python
"""Database connection and helpers for scrapers."""
import os
import libsql_client
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ["TURSO_DATABASE_URL"]
DB_TOKEN = os.environ["TURSO_AUTH_TOKEN"]

_client = None

def get_client():
    global _client
    if _client is None:
        _client = libsql_client.create_client_sync(
            url=DB_URL,
            auth_token=DB_TOKEN,
        )
    return _client

def execute(sql: str, params: list | None = None):
    """Execute a SQL statement."""
    client = get_client()
    return client.execute(sql, params or [])

def batch_execute(statements: list[tuple[str, list]]):
    """Execute multiple SQL statements in a transaction."""
    client = get_client()
    stmts = [libsql_client.Statement(sql, params) for sql, params in statements]
    return client.batch(stmts)

def query(sql: str, params: list | None = None) -> list[dict]:
    """Run a SELECT query and return rows as dicts."""
    client = get_client()
    result = client.execute(sql, params or [])
    columns = [col.name for col in result.columns]
    return [dict(zip(columns, row)) for row in result.rows]
```

**Step 2: Test connection**

```python
# Run: python -c "
from scrapers.db import query
stores = query('SELECT * FROM stores')
print(stores)
# Expected: [{'id': 'iga-vashon', ...}, {'id': 'thriftway-vashon', ...}]
"
```

**Verification:** Python can connect to Turso and read the seeded store records.

---

## PHASE 2: IGA Data Pipeline (Day 2-3)

### Task 2.1: Build IGA Freshop API scraper — departments

**Objective:** Scrape all IGA departments from Freshop API and store in DB

**Files:**
- Modify: `scrapers/scrapers/iga.py`

**Step 1: Write department fetcher**

```python
"""IGA Vashon Market scraper — Freshop API."""
import time
import httpx
from scrapers.db import execute, query

BASE_URL = "https://api.freshop.ncrcloud.com"
APP_KEY = "vashon_fresh_market"
STORE_ID = "7432"

def fetch(path: str, params: dict | None = None) -> dict:
    """Call Freshop API with app_key."""
    url = f"{BASE_URL}{path}"
    if "?" not in url:
        url += f"?app_key={APP_KEY}"
    response = httpx.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def scrape_departments():
    """Fetch all IGA departments and insert into DB."""
    data = fetch(f"/departments", {"store_id": STORE_ID})
    departments = data if isinstance(data, list) else data.get("items", data.get("departments", []))
    
    inserted = 0
    for dept in departments:
        dept_id = str(dept.get("id", dept.get("department_id")))
        name = dept.get("name", dept.get("department_name", ""))
        parent_id = str(dept.get("parent_id")) if dept.get("parent_id") else None
        
        execute(
            """INSERT OR REPLACE INTO departments (id, store_id, name, parent_id)
               VALUES (?, ?, ?, ?)""",
            [dept_id, "iga-vashon", name, parent_id]
        )
        inserted += 1
    
    print(f"Inserted/updated {inserted} departments for IGA")
    return inserted

if __name__ == "__main__":
    scrape_departments()
```

**Step 2: Run it**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
source .venv/bin/activate
python -m scrapers.iga
```

**Verification:** Prints department count (should be 1,000+). `turso db shell grocery-store-wars "SELECT COUNT(*) FROM departments WHERE store_id='iga-vashon';"` returns matching count.

---

### Task 2.2: Build IGA product scraper — paginated fetch

**Objective:** Scrape all 12,018 IGA products with full details

**Files:**
- Modify: `scrapers/scrapers/iga.py`

**Step 1: Add product scraping function**

Append to `iga.py`:

```python
def scrape_products(batch_size: int = 100, delay: float = 1.0):
    """Paginate through all IGA products and insert into DB."""
    offset = 0
    total = 0
    
    while True:
        data = fetch(
            "/products",
            {"store_id": STORE_ID, "limit": batch_size, "offset": offset}
        )
        items = data if isinstance(data, list) else data.get("items", data.get("products", []))
        
        if not items:
            break
        
        for product in items:
            _insert_product(product)
            total += 1
        
        offset += batch_size
        print(f"Scraped {total} products (offset {offset})...")
        time.sleep(delay)  # Be polite
    
    # Update store metadata
    execute(
        "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = 'iga-vashon'",
        [total]
    )
    print(f"Done. Total: {total} IGA products")
    return total

def _insert_product(product: dict):
    """Insert or update a single product."""
    pid = str(product.get("id"))
    execute(
        """INSERT OR REPLACE INTO products (
            id, store_id, name, price, unit_price, price_display,
            upc, barcode, barcode_type, size, brand, manufacturer,
            department_id, category, image_url, product_url,
            is_weight_required, quantity_label, last_updated_at, is_iga
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            pid,
            "iga-vashon",
            product.get("name", ""),
            product.get("unit_price") or product.get("price"),
            product.get("unit_price"),
            product.get("price") if isinstance(product.get("price"), str) else None,
            str(product.get("upc")) if product.get("upc") else None,
            product.get("barcode") or product.get("barcode_upc_a"),
            product.get("barcode_type", "UPC-A"),
            product.get("size"),
            product.get("brand"),
            product.get("manufacturer"),
            str(product.get("department_ids", [None])[0]) if product.get("department_ids") else None,
            product.get("category"),
            _build_image_url(product),
            product.get("canonical_url"),
            1 if product.get("is_weight_required") else 0,
            product.get("quantity_label"),
            product.get("last_updated_at", None),
            1,  # is_iga = true
        ]
    )
    
    # Record price history
    price = product.get("unit_price") or product.get("price")
    if price:
        execute(
            "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
            [pid, "iga-vashon", float(price)]
        )

def _build_image_url(product: dict) -> str | None:
    """Build CDN image URL from product image data."""
    images = product.get("images", [])
    if images and isinstance(images, list) and len(images) > 0:
        identifier = images[0].get("identifier", "")
        if identifier:
            return f"https://images.freshop.ncrcloud.com/{identifier}_medium.jpg"
    return None
```

**Step 2: Run full scrape**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
source .venv/bin/activate
python -c "from scrapers.iga import scrape_products; scrape_products()"
```

This takes ~2-3 hours for 12K products at 1s delay. Kill early with Ctrl+C to verify it's working, then restart.

**Verification:** `turso db shell grocery-store-wars "SELECT COUNT(*) FROM products WHERE is_iga=1;"` returns growing count. Sample: `SELECT name, price_display FROM products WHERE is_iga=1 LIMIT 5;` shows real products.

---

### Task 2.3: Thriftway Freshop catalog scraper

**Objective:** Scrape Thriftway's stale Freshop data (70K products) for catalog matching

**Files:**
- Modify: `scrapers/scrapers/thriftway.py`

**Step 1: Write Thriftway Freshop scraper**

```python
"""Thriftway scraper — Freshop catalog (stale) + Mercato prices (current, limited)."""
import time
import httpx
from scrapers.db import execute

FRESHOP_BASE = "https://api.freshop.ncrcloud.com"
FRESHOP_APP_KEY = "vashon_thriftway"
FRESHOP_STORE_ID = "1813"

def fetch_freshop(path: str, params: dict | None = None) -> dict:
    url = f"{FRESHOP_BASE}{path}"
    if "?" not in url:
        url += f"?app_key={FRESHOP_APP_KEY}"
    response = httpx.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def scrape_thriftway_catalog(batch_size: int = 100, delay: float = 0.5, max_products: int | None = None):
    """Scrape Thriftway product catalog from Freshop (prices are stale — metadata is good)."""
    offset = 0
    total = 0
    
    while True:
        data = fetch_freshop(
            "/products",
            {"store_id": FRESHOP_STORE_ID, "limit": batch_size, "offset": offset}
        )
        items = data if isinstance(data, list) else data.get("items", data.get("products", []))
        
        if not items:
            break
        
        for product in items:
            pid = f"tw-freshop-{product.get('id')}"
            execute(
                """INSERT OR REPLACE INTO products (
                    id, store_id, name, price, unit_price, price_display,
                    upc, barcode, size, brand, department_id, category,
                    image_url, product_url, last_updated_at, is_iga
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    pid,
                    "thriftway-vashon",
                    product.get("name", ""),
                    product.get("unit_price"),  # STALE — will be overridden
                    product.get("unit_price"),
                    product.get("price") if isinstance(product.get("price"), str) else None,
                    str(product.get("upc")) if product.get("upc") else None,
                    product.get("barcode") or product.get("barcode_upc_a"),
                    product.get("size"),
                    product.get("brand"),
                    str(product.get("department_ids", [None])[0]) if product.get("department_ids") else None,
                    product.get("category"),
                    f"https://images.freshop.ncrcloud.com/{product.get('images', [{}])[0].get('identifier', '')}_medium.jpg" if product.get("images") else None,
                    product.get("canonical_url"),
                    "2020-03-01",  # Known stale date
                    0,  # is_iga = false
                ]
            )
            total += 1
        
        offset += batch_size
        print(f"Thriftway catalog: {total} products (offset {offset})...")
        
        if max_products and total >= max_products:
            break
        
        time.sleep(delay)
    
    execute(
        "UPDATE stores SET product_count = ?, last_scraped_at = datetime('now') WHERE id = 'thriftway-vashon'",
        [total]
    )
    print(f"Done. Total: {total} Thriftway catalog products")
    return total

if __name__ == "__main__":
    scrape_thriftway_catalog()
```

**Step 2: Run initial batch (test)**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
source .venv/bin/activate
python -c "from scrapers.thriftway import scrape_thriftway_catalog; scrape_thriftway_catalog(max_products=500)"
```

**Step 3: Full run**

```bash
# Remove max_products limit and let it run overnight
python -c "from scrapers.thriftway import scrape_thriftway_catalog; scrape_thriftway_catalog()"
```

70K products at 0.5s delay = ~10 hours. Run it once, it's a one-time operation for the catalog.

**Verification:** `turso db shell grocery-store-wars "SELECT COUNT(*) FROM products WHERE is_iga=0;"` shows growing Thriftway count.

---

## PHASE 3: Thriftway Price Verification (Day 3-4)

### Task 3.1: Manual Mercato scraper for staple items

**Objective:** Build a Playwright script that carefully scrapes current prices for 200-300 staple items from Mercato, with heavy human-like delays

**Files:**
- Create: `scrapers/scrapers/mercato.py`

**Step 1: Write Mercato staple scraper**

```python
"""Mercato price scraper for Thriftway — staple items only.
Uses Playwright with heavy delays to appear human. No proxy required
for 200-300 items scraped slowly once per week."""
import time
import random
import asyncio
from playwright.async_api import async_playwright

MERCATO_BASE = "https://www.mercato.com/shop/vashon-thriftway"

# Staples to check — these matter most for the KPI dashboard
STAPLE_SEARCHES = [
    "milk whole gallon",
    "eggs large dozen",
    "ground beef 80/20",
    "mayonnaise hellmann",
    "bread sourdough",
    "butter unsalted",
    "chicken breast",
    "cheese cheddar",
    "yogurt greek",
    "coffee ground",
    "bananas",
    "lettuce romaine",
    "tomatoes",
    "potatoes russet",
    "onions yellow",
    "orange juice",
    "bacon",
    "sausage",
    "lunch meat turkey",
    "cereal cheerios",
    "pasta spaghetti",
    "rice white",
    "canned tuna",
    "peanut butter",
    "jelly grape",
    "chips potato",
    "soda cola",
    "water bottled",
    "paper towels",
    "toilet paper",
    "dish soap",
    "laundry detergent",
    "flour all-purpose",
    "sugar white",
    "oil olive",
]

async def human_delay(min_s=3, max_s=8):
    """Random delay between actions."""
    await asyncio.sleep(random.uniform(min_s, max_s))

async def type_like_human(page, selector, text):
    """Type character by character with random delays."""
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char, delay=random.randint(30, 120))
        if random.random() < 0.1:  # 10% chance of brief pause mid-word
            await asyncio.sleep(random.uniform(0.1, 0.3))

async def scrape_staples():
    """Search for each staple item on Mercato and extract top result price."""
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()
        
        # Load Mercato store page first (appears as real visitor)
        await page.goto(MERCATO_BASE, wait_until="networkidle", timeout=30000)
        await human_delay(3, 6)
        
        # Handle zip code prompt if it appears
        try:
            zip_input = page.locator('input[placeholder*="zip"]').first
            if await zip_input.is_visible(timeout=3000):
                await type_like_human(page, 'input[placeholder*="zip"]', "98070")
                await page.keyboard.press("Enter")
                await human_delay(2, 5)
        except Exception:
            pass  # No zip prompt
        
        for query in STAPLE_SEARCHES:
            try:
                # Find search box and type query
                search_selectors = [
                    'input[type="search"]',
                    'input[placeholder*="Search"]',
                    'input[placeholder*="search"]',
                    '[data-testid="search-input"]',
                ]
                
                search_box = None
                for sel in search_selectors:
                    search_box = page.locator(sel).first
                    if await search_box.is_visible(timeout=2000):
                        break
                
                if not search_box:
                    print(f"  No search box found for '{query}' — skipping")
                    continue
                
                await search_box.click()
                await search_box.fill("")  # Clear
                await type_like_human(page, search_selectors[0], query)  # Reuse first selector
                await page.keyboard.press("Enter")
                await human_delay(4, 8)  # Wait for results to load
                
                # Extract product names and prices from results
                products = await page.evaluate("""() => {
                    const items = [];
                    document.querySelectorAll('[data-testid="product-card"], .product-card, [class*="product"]').forEach(card => {
                        const name = card.querySelector('h3, h4, [class*="name"], [class*="title"]')?.textContent?.trim();
                        const price = card.querySelector('[class*="price"], [data-testid="product-price"]')?.textContent?.trim();
                        if (name && price) items.push({name, price});
                    });
                    return items.slice(0, 5);  // Top 5 results
                }""")
                
                if products:
                    results.append({
                        "query": query,
                        "top_result": products[0],
                        "all_results": products,
                    })
                    print(f"  '{query}' → {products[0]['name'][:60]} @ {products[0]['price']}")
                else:
                    print(f"  '{query}' → no results found")
                
                # Navigate back to store page for next search
                await page.goto(MERCATO_BASE, wait_until="networkidle", timeout=30000)
                await human_delay(5, 12)  # Longer delay between searches
                
            except Exception as e:
                print(f"  Error on '{query}': {e}")
                # Try to recover
                try:
                    await page.goto(MERCATO_BASE, wait_until="networkidle", timeout=30000)
                    await human_delay(5, 10)
                except Exception:
                    pass
        
        await browser.close()
    
    return results

async def main():
    print("Starting Mercato staple price check...")
    print(f"Checking {len(STAPLE_SEARCHES)} staple items with human-like behavior\n")
    
    results = await scrape_staples()
    
    print(f"\n--- Results ---")
    print(f"Successfully checked: {len(results)}/{len(STAPLE_SEARCHES)} items")
    for r in results:
        print(f"  {r['query']}: {r['top_result']['name'][:50]} — {r['top_result']['price']}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Test with 3 items first**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
source .venv/bin/activate
# Edit STAPLE_SEARCHES to just 3 items first for testing
python -c "
import asyncio
from scrapers.mercato import scrape_staples
asyncio.run(scrape_staples())
"
```

**Step 3: If Mercato blocks, document the fallback**

If Playwright gets blocked (Cloudflare challenge), add to `mercato.py`:

```python
# Fallback: screenshot what we can, log the rest
async def scrape_with_fallback():
    try:
        return await scrape_staples()
    except Exception as e:
        print(f"Mercato blocked: {e}")
        print("Falling back to shelf-tag photo upload flow (V2 feature)")
        return []
```

**Verification:** Run on 3 test items — if results come back, it works. If blocked, we pivot to V2 shelf-tag approach now.

---

### Task 3.2: Price update script for Thriftway Freshop data

**Objective:** Take Mercato-scraped prices and update matching Thriftway products in DB

**Files:**
- Create: `scrapers/scrapers/price_updater.py`

**Step 1: Write price updater**

```python
"""Match Mercato prices to Thriftway Freshop products and update DB."""
from thefuzz import fuzz
from scrapers.db import query, execute

def update_thriftway_prices(mercato_results: list[dict]):
    """For each Mercato result, find best Freshop match by name and update price."""
    updated = 0
    
    for result in mercato_results:
        top = result["top_result"]
        mercato_name = top["name"]
        mercato_price = _parse_price(top["price"])
        
        if mercato_price is None:
            continue
        
        # Search for matching products in Thriftway Freshop catalog
        candidates = query(
            """SELECT id, name, price FROM products
               WHERE store_id = 'thriftway-vashon'
               AND name LIKE ?
               LIMIT 20""",
            [f"%{result['query'].split()[0]}%"]
        )
        
        best_match = None
        best_score = 0
        
        for c in candidates:
            score = fuzz.token_sort_ratio(mercato_name.lower(), c["name"].lower())
            if score > best_score:
                best_score = score
                best_match = c
        
        if best_match and best_score > 60:
            execute(
                """UPDATE products SET
                   price = ?, price_display = ?, last_updated_at = datetime('now')
                   WHERE id = ?""",
                [mercato_price, top["price"], best_match["id"]]
            )
            execute(
                "INSERT INTO price_history (product_id, store_id, price) VALUES (?, ?, ?)",
                [best_match["id"], "thriftway-vashon", mercato_price]
            )
            updated += 1
            print(f"  Updated '{best_match['name'][:50]}' → ${mercato_price} (score: {best_score})")
        else:
            print(f"  No match for '{mercato_name[:50]}' (best: {best_score})")
    
    print(f"\nUpdated {updated} Thriftway prices from Mercato")
    return updated

def _parse_price(price_str: str) -> float | None:
    """Parse price string like '$4.99' or '4.99' to float."""
    import re
    match = re.search(r'[\d.]+', str(price_str))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None
```

**Verification:** After running Mercato scraper, run price updater and verify: `SELECT name, price_display FROM products WHERE store_id='thriftway-vashon' AND last_updated_at > date('now', '-1 day') LIMIT 10;`

---

## PHASE 4: Product Matching Engine (Day 4-5)

### Task 4.1: Build fuzzy product matcher

**Objective:** Match IGA products to Thriftway products using UPC + fuzzy name matching

**Files:**
- Modify: `scrapers/scrapers/matcher.py`

**Step 1: Write matching engine**

```python
"""Product matching engine — UPC exact + fuzzy name matching."""
from thefuzz import fuzz
from scrapers.db import query, batch_execute

# Configurable thresholds
UPC_MATCH_CONFIDENCE = 1.0      # Exact UPC match = 100%
FUZZY_NAME_THRESHOLD = 85       # Token sort ratio minimum
SIZE_BONUS = 0.05               # Bonus if sizes match
BRAND_BONUS = 0.05              # Bonus if brands match

def match_all(min_confidence: float = 0.70):
    """Match all unmatched IGA products to Thriftway products."""
    iga_products = query("SELECT id, name, upc, barcode, size, brand FROM products WHERE is_iga=1")
    tw_products = query("SELECT id, name, upc, barcode, size, brand FROM products WHERE is_iga=0")
    
    # Build lookup: UPC → Thriftway products
    tw_by_upc = {}
    for p in tw_products:
        for code_field in [p["upc"], p["barcode"]]:
            if code_field:
                # Normalize: strip leading zero padding, trim to 12 digits
                code = str(code_field).strip().lstrip("0").zfill(12)
                tw_by_upc[code] = p
    
    matched = 0
    statements = []
    
    for iga in iga_products:
        best_id = None
        best_confidence = 0.0
        match_type = "fuzzy_name"
        
        # Strategy 1: Exact UPC match
        iga_upcs = _get_upcs(iga)
        for upc in iga_upcs:
            if upc in tw_by_upc:
                best_id = tw_by_upc[upc]["id"]
                best_confidence = UPC_MATCH_CONFIDENCE
                match_type = "upc_exact"
                break
        
        # Strategy 2: Fuzzy name matching (if no UPC match)
        if best_confidence < UPC_MATCH_CONFIDENCE:
            iga_name = _normalize(iga["name"])
            iga_size = _normalize(iga.get("size", ""))
            iga_brand = _normalize(iga.get("brand", ""))
            
            for tw in tw_products:
                tw_name = _normalize(tw["name"])
                name_score = fuzz.token_sort_ratio(iga_name, tw_name)
                
                if name_score < FUZZY_NAME_THRESHOLD:
                    continue
                
                confidence = name_score / 100.0
                
                # Bonus for matching size
                tw_size = _normalize(tw.get("size", ""))
                if iga_size and tw_size and iga_size == tw_size:
                    confidence += SIZE_BONUS
                
                # Bonus for matching brand
                tw_brand = _normalize(tw.get("brand", ""))
                if iga_brand and tw_brand and iga_brand == tw_brand:
                    confidence += BRAND_BONUS
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_id = tw["id"]
                    match_type = "fuzzy_name"
        
        # Insert match if above threshold
        if best_id and best_confidence >= min_confidence:
            statements.append((
                """INSERT OR REPLACE INTO product_matches
                   (iga_product_id, thriftway_product_id, match_type, confidence, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                [iga["id"], best_id, match_type, min(best_confidence, 1.0)]
            ))
            matched += 1
    
    if statements:
        batch_execute(statements)
    
    print(f"Matched {matched}/{len(iga_products)} IGA products to Thriftway")
    return matched

def _get_upcs(product: dict) -> list[str]:
    """Extract and normalize all UPCs from a product."""
    upcs = []
    for field in ["upc", "barcode"]:
        val = product.get(field)
        if val:
            code = str(val).strip().lstrip("0")
            upcs.append(code)
            upcs.append(code.zfill(12))
    return list(set(upcs))

def _normalize(s: str | None) -> str:
    """Normalize string for comparison."""
    if not s:
        return ""
    return s.lower().strip().replace("'s", "s").replace("  ", " ")

if __name__ == "__main__":
    match_all()
```

**Step 2: Run the matcher**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
source .venv/bin/activate
python -m scrapers.matcher
```

**Verification:** Prints match count. `turso db shell grocery-store-wars "SELECT match_type, COUNT(*) FROM product_matches GROUP BY match_type;"` shows breakdown. `SELECT confidence, COUNT(*) FROM product_matches GROUP BY round(confidence*10)/10 ORDER BY confidence DESC;` shows confidence distribution.

---

### Task 4.2: Seed staple items

**Objective:** Create the KPI staple items (milk, eggs, meat, bread, mayo) in the database

**Files:**
- Create: `scrapers/scrapers/seed_staples.py`

**Step 1: Write seed script**

```python
"""Seed staple items for KPI dashboard.
Searches for common products by name and links them."""
from thefuzz import fuzz
from scrapers.db import query, execute

STAPLES = [
    ("Milk (1 gal)", "milk whole gallon", "dairy", 1),
    ("Eggs (12 ct)", "eggs large dozen", "dairy", 2),
    ("Ground Beef 80/20", "ground beef 80", "meat", 3),
    ("Chicken Breast", "chicken breast boneless", "meat", 4),
    ("Sourdough Bread", "sourdough bread", "bakery", 5),
    ("Mayonnaise (30oz)", "mayonnaise hellmann", "pantry", 6),
    ("Butter (1 lb)", "butter unsalted", "dairy", 7),
    ("Cheddar Cheese", "cheese cheddar", "dairy", 8),
    ("Bananas", "bananas", "produce", 9),
    ("Coffee (12oz)", "coffee ground", "pantry", 10),
    ("Bacon", "bacon", "meat", 11),
    ("Toilet Paper", "toilet paper", "household", 12),
    ("Laundry Detergent", "laundry detergent", "household", 13),
    ("Olive Oil", "oil olive", "pantry", 14),
    ("Orange Juice", "orange juice", "beverages", 15),
]

def seed():
    for name, search, category, order in STAPLES:
        # Find best IGA product
        iga = _find_best(search, is_iga=1)
        tw = _find_best(search, is_iga=0)
        
        execute(
            """INSERT OR REPLACE INTO staple_items
               (name, iga_product_id, thriftway_product_id, category, display_order)
               VALUES (?, ?, ?, ?, ?)""",
            [
                name,
                iga["id"] if iga else None,
                tw["id"] if tw else None,
                category,
                order,
            ]
        )
        iga_price = iga.get("price_display", "N/A") if iga else "N/A"
        tw_price = tw.get("price_display", "N/A") if tw else "N/A"
        print(f"  {name}: IGA {iga_price} | TW {tw_price}")

def _find_best(search: str, is_iga: int) -> dict | None:
    terms = search.split()
    candidates = query(
        f"""SELECT id, name, price_display FROM products
            WHERE is_iga = ? AND (name LIKE ? OR name LIKE ?)
            LIMIT 30""",
        [is_iga, f"%{terms[0]}%", f"%{terms[1]}%" if len(terms) > 1 else f"%{terms[0]}%"]
    )
    if not candidates:
        return None
    
    best = max(candidates, key=lambda c: fuzz.partial_ratio(search, c["name"].lower()))
    return best

if __name__ == "__main__":
    seed()
```

**Step 2: Run seed**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
source .venv/bin/activate
python -m scrapers.seed_staples
```

**Verification:** `turso db shell grocery-store-wars "SELECT * FROM staple_items;"` shows 15 rows with product IDs.

---

## PHASE 5: Next.js API Layer (Day 5-6)

### Task 5.1: Set up Turso client in Next.js

**Objective:** Next.js can query Turso database from API routes

**Files:**
- Modify: `frontend/src/db/index.ts`
- Create: `frontend/src/db/queries.ts`

**Step 1: Install and configure libsql client**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm install @libsql/client
```

Ensure `frontend/src/db/index.ts` has the content from Task 1.1 Step 3.

Create `frontend/src/db/queries.ts`:

```typescript
import turso from "./index";

// --- Dashboard ---
export async function getDashboardStats() {
  const result = await turso.execute(`
    SELECT
      (SELECT COUNT(*) FROM products WHERE is_iga = 1) as iga_count,
      (SELECT COUNT(*) FROM products WHERE is_iga = 0) as tw_count,
      (SELECT COUNT(*) FROM product_matches) as matched_count,
      (SELECT AVG(iga.price - tw.price) FROM product_matches pm
       JOIN products iga ON pm.iga_product_id = iga.id
       JOIN products tw ON pm.thriftway_product_id = tw.id
       WHERE iga.price IS NOT NULL AND tw.price IS NOT NULL) as avg_price_gap
  `);
  return result.rows[0];
}

// --- Staple Items ---
export async function getStapleItems() {
  const result = await turso.execute(`
    SELECT si.*,
      iga.name as iga_name, iga.price as iga_price, iga.price_display as iga_display,
      tw.name as tw_name, tw.price as tw_price, tw.price_display as tw_display
    FROM staple_items si
    LEFT JOIN products iga ON si.iga_product_id = iga.id
    LEFT JOIN products tw ON si.thriftway_product_id = tw.id
    ORDER BY si.display_order
  `);
  return result.rows;
}

// --- Product Search ---
export async function searchProducts(query: string, limit = 20) {
  const result = await turso.execute({
    sql: `
      SELECT p.*, pm.thriftway_product_id, pm.confidence as match_confidence,
        tw.price as competitor_price, tw.price_display as competitor_display,
        tw.name as competitor_name
      FROM products p
      LEFT JOIN product_matches pm ON p.id = pm.iga_product_id
      LEFT JOIN products tw ON pm.thriftway_product_id = tw.id
      WHERE p.is_iga = 1 AND p.name LIKE ?
      LIMIT ?
    `,
    args: [`%${query}%`, limit],
  });
  return result.rows;
}

// --- UPC Lookup ---
export async function lookupByUPC(upc: string) {
  const result = await turso.execute({
    sql: `
      SELECT p.*, pm.thriftway_product_id, pm.match_type, pm.confidence,
        tw.price as competitor_price, tw.price_display as competitor_display,
        tw.name as competitor_name
      FROM products p
      LEFT JOIN product_matches pm ON p.id = pm.iga_product_id
      LEFT JOIN products tw ON pm.thriftway_product_id = tw.id
      WHERE p.is_iga = 1 AND (p.upc = ? OR p.barcode = ?)
      LIMIT 5
    `,
    args: [upc, upc],
  });
  return result.rows;
}

// --- Department Comparison ---
export async function getDepartmentComparison(departmentId?: string) {
  let sql = `
    SELECT p.department_id, d.name as department_name,
      COUNT(*) as product_count,
      AVG(p.price) as avg_iga_price,
      AVG(tw.price) as avg_tw_price,
      AVG(p.price - tw.price) as avg_gap
    FROM products p
    JOIN product_matches pm ON p.id = pm.iga_product_id
    JOIN products tw ON pm.thriftway_product_id = tw.id
    LEFT JOIN departments d ON p.department_id = d.id
    WHERE p.is_iga = 1 AND p.price IS NOT NULL AND tw.price IS NOT NULL
  `;
  if (departmentId) {
    sql += ` AND p.department_id = '${departmentId}'`;
  }
  sql += ` GROUP BY p.department_id ORDER BY ABS(AVG(p.price - tw.price)) DESC LIMIT 20`;

  const result = await turso.execute(sql);
  return result.rows;
}

// --- Margin Opportunities ---
export async function getMarginOpportunities(limit = 10) {
  const result = await turso.execute({
    sql: `
      SELECT p.name, p.price as iga_price, p.price_display as iga_display,
        tw.price as tw_price, tw.price_display as tw_display,
        (tw.price - p.price) as gap,
        (tw.price - 0.05) as suggested_price
      FROM products p
      JOIN product_matches pm ON p.id = pm.iga_product_id
      JOIN products tw ON pm.thriftway_product_id = tw.id
      WHERE p.is_iga = 1
        AND p.price IS NOT NULL
        AND tw.price IS NOT NULL
        AND p.price < tw.price
      ORDER BY (tw.price - p.price) DESC
      LIMIT ?
    `,
    args: [limit],
  });
  return result.rows;
}

// --- Price History ---
export async function getPriceHistory(productId: string, days = 30) {
  const result = await turso.execute({
    sql: `
      SELECT ph.*, s.name as store_name
      FROM price_history ph
      JOIN stores s ON ph.store_id = s.id
      WHERE ph.product_id = ?
        AND ph.recorded_at >= datetime('now', ? || ' days')
      ORDER BY ph.recorded_at DESC
      LIMIT 100
    `,
    args: [productId, `-${days}`],
  });
  return result.rows;
}
```

**Verification:** Import in a temp file and test: `npx tsx -e "import { getStapleItems } from './src/db/queries'; getStapleItems().then(console.log)"` — should return staple items.

---

### Task 5.2: Create API routes

**Objective:** Build REST API endpoints that the frontend calls

**Files:**
- Create: `frontend/src/app/api/dashboard/route.ts`
- Create: `frontend/src/app/api/products/search/route.ts`
- Create: `frontend/src/app/api/products/upc/route.ts`
- Create: `frontend/src/app/api/departments/route.ts`
- Create: `frontend/src/app/api/margins/route.ts`
- Create: `frontend/src/app/api/staples/route.ts`

**Step 1: Dashboard stats API**

Create `frontend/src/app/api/dashboard/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { getDashboardStats, getStapleItems, getMarginOpportunities } from "@/db/queries";

export async function GET() {
  const stats = await getDashboardStats();
  const staples = await getStapleItems();
  const margins = await getMarginOpportunities(10);

  return NextResponse.json({ stats, staples, margins });
}
```

**Step 2: Product search API**

Create `frontend/src/app/api/products/search/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { searchProducts } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q");
  if (!q) return NextResponse.json({ error: "Missing q parameter" }, { status: 400 });
  
  const results = await searchProducts(q);
  return NextResponse.json(results);
}
```

**Step 3: UPC lookup API**

Create `frontend/src/app/api/products/upc/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { lookupByUPC } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const upc = searchParams.get("code");
  if (!upc) return NextResponse.json({ error: "Missing code parameter" }, { status: 400 });
  
  const results = await lookupByUPC(upc);
  return NextResponse.json(results);
}
```

**Step 4: Department comparison API**

Create `frontend/src/app/api/departments/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { getDepartmentComparison } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const deptId = searchParams.get("id");
  const results = await getDepartmentComparison(deptId || undefined);
  return NextResponse.json(results);
}
```

**Step 5: Margin opportunities API**

Create `frontend/src/app/api/margins/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { getMarginOpportunities } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "10");
  const results = await getMarginOpportunities(limit);
  return NextResponse.json(results);
}
```

**Step 6: Staple items API**

Create `frontend/src/app/api/staples/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { getStapleItems } from "@/db/queries";

export async function GET() {
  const results = await getStapleItems();
  return NextResponse.json(results);
}
```

**Verification:** Start `npm run dev`, visit `http://localhost:3000/api/dashboard` — should return JSON with stats, staples, margins. `http://localhost:3000/api/products/search?q=milk` returns product array.

---

## PHASE 6: Authentication (Day 6)

### Task 6.1: Set up NextAuth.js with email/password

**Objective:** Password-protect the dashboard. Single admin user for MVP.

**Files:**
- Create: `frontend/src/auth.ts`
- Create: `frontend/src/app/api/auth/[...nextauth]/route.ts`
- Create: `frontend/src/middleware.ts`

**Step 1: Install NextAuth**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm install next-auth@beta
```

**Step 2: Create auth configuration**

Create `frontend/src/auth.ts`:

```typescript
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import turso from "@/db";
import bcrypt from "bcryptjs";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const result = await turso.execute({
          sql: "SELECT * FROM users WHERE email = ?",
          args: [credentials.email as string],
        });

        const user = result.rows[0] as any;
        if (!user) return null;

        const valid = await bcrypt.compare(
          credentials.password as string,
          user.password_hash
        );
        if (!valid) return null;

        return { id: user.id, email: user.email, name: user.name };
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: { strategy: "jwt" },
});
```

**Step 3: Create auth API route**

Create `frontend/src/app/api/auth/[...nextauth]/route.ts`:

```typescript
import { handlers } from "@/auth";
export const { GET, POST } = handlers;
```

**Step 4: Create middleware to protect routes**

Create `frontend/src/middleware.ts`:

```typescript
export { auth as middleware } from "@/auth";

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|login).*)"],
};
```

**Step 5: Install bcryptjs and seed admin user**

```bash
npm install bcryptjs
npm install -D @types/bcryptjs
```

Create seed user script:

```bash
npx tsx -e "
const bcrypt = require('bcryptjs');
const hash = bcrypt.hashSync('changeme123', 10);
console.log('Hashed password:', hash);
"
```

Insert into Turso:

```bash
turso db shell grocery-store-wars "INSERT INTO users (id, email, name, password_hash) VALUES ('admin-1', 'admin@grocery-store-wars.com', 'Store Owner', '[hash-from-above]');"
```

**Verification:** `npm run dev`, visit `http://localhost:3000` — should redirect to `/login`. Login with `admin@grocery-store-wars.com` / `changeme123` — should reach dashboard (blank for now).

---

## PHASE 7: Frontend Pages (Day 6-12)

### Task 7.1: Root layout with auth and navigation

**Objective:** Create the app shell — sidebar nav, auth wrapper, basic layout

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Create: `frontend/src/components/nav.tsx`
- Create: `frontend/src/components/app-shell.tsx`

**Step 1: Root layout**

Replace `frontend/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Grocery Store Wars",
  description: "Competitive pricing intelligence for independent grocers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
```

**Step 2: Navigation sidebar**

Create `frontend/src/components/nav.tsx`:

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Search, Store, TrendingUp, FileText, Settings, Camera } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/search", label: "Search", icon: Search },
  { href: "/departments", label: "Departments", icon: Store },
  { href: "/margins", label: "Margins", icon: TrendingUp },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="w-64 border-r bg-white p-4 space-y-1">
      <div className="mb-8 px-2">
        <h1 className="text-lg font-bold tracking-tight">Grocery Store Wars</h1>
        <p className="text-xs text-gray-500">Pricing Intelligence</p>
      </div>
      {links.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
            pathname === href
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:bg-gray-100"
          )}
        >
          <Icon className="h-4 w-4" />
          {label}
        </Link>
      ))}
    </nav>
  );
}
```

**Step 3: App shell wrapper**

Create `frontend/src/components/app-shell.tsx`:

```tsx
import { auth } from "@/auth";
import { Nav } from "./nav";
import { redirect } from "next/navigation";

export async function AppShell({ children }: { children: React.ReactNode }) {
  const session = await auth();
  
  // Public routes
  if (!session) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Nav />
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}
```

**Step 4: Create shadcn utility file**

Create `frontend/src/lib/utils.ts`:

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

Install deps:
```bash
npm install clsx tailwind-merge
```

**Verification:** `npm run dev` — sidebar renders. Links navigate. Unauthenticated users stay on login page (blank for now).

---

### Task 7.2: Login page

**Objective:** Clean login page with store branding

**Files:**
- Create: `frontend/src/app/login/page.tsx`
- Create: `frontend/src/components/login-form.tsx`

**Step 1: Login page**

Create `frontend/src/app/login/page.tsx`:

```tsx
import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">Grocery Store Wars</h1>
          <p className="text-gray-500 mt-1">Sign in to your dashboard</p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
```

**Step 2: Login form component**

Create `frontend/src/components/login-form.tsx`:

```tsx
"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    if (result?.error) {
      setError("Invalid email or password");
      setLoading(false);
    } else {
      router.push("/");
      router.refresh();
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@store.com"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

**Verification:** Visit `http://localhost:3000/login` — form renders. Submit with test credentials -> redirects to dashboard.

---

### Task 7.3: Dashboard page (home)

**Objective:** KPI cards, staple price tracker, department overview, margin opportunities

**Files:**
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/dashboard/kpi-cards.tsx`
- Create: `frontend/src/components/dashboard/staple-tracker.tsx`
- Create: `frontend/src/components/dashboard/margin-opps.tsx`

**Step 1: Dashboard page**

Create `frontend/src/app/page.tsx`:

```tsx
import { KPICards } from "@/components/dashboard/kpi-cards";
import { StapleTracker } from "@/components/dashboard/staple-tracker";
import { MarginOpps } from "@/components/dashboard/margin-opps";

export default async function DashboardPage() {
  // Fetch data server-side
  const res = await fetch(`${process.env.NEXTAUTH_URL}/api/dashboard`, {
    cache: "no-store",
  });
  const data = await res.json();

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-gray-500 mt-1">Competitive pricing overview</p>
      </div>

      <KPICards stats={data.stats} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <StapleTracker staples={data.staples} />
        <MarginOpps margins={data.margins} />
      </div>
    </div>
  );
}
```

**Step 2: KPI cards**

Create `frontend/src/components/dashboard/kpi-cards.tsx`:

```tsx
import { Card, CardContent } from "@/components/ui/card";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";

export function KPICards({ stats }: { stats: any }) {
  const gap = stats?.avg_price_gap || 0;
  const igaWins = gap < 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500">IGA Products</p>
          <p className="text-2xl font-bold">{stats?.iga_count?.toLocaleString() || 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500">Thriftway Products</p>
          <p className="text-2xl font-bold">{stats?.tw_count?.toLocaleString() || 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500">Matched Products</p>
          <p className="text-2xl font-bold">{stats?.matched_count?.toLocaleString() || 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500">Avg Price Gap</p>
          <p className={`text-2xl font-bold ${igaWins ? "text-green-600" : "text-red-600"}`}>
            {gap > 0 ? "+" : ""}{gap.toFixed(2)}
          </p>
          <p className="text-xs text-gray-400">
            {igaWins ? "IGA is cheaper on average" : "IGA is pricier on average"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Step 3: Staple tracker**

Create `frontend/src/components/dashboard/staple-tracker.tsx`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function StapleTracker({ staples }: { staples: any[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Staple Price Watch</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {(staples || []).map((item: any) => {
            const igaPrice = item.iga_price;
            const twPrice = item.tw_price;
            if (!igaPrice || !twPrice) return null;
            const diff = igaPrice - twPrice;
            const igaWins = diff < 0;

            return (
              <div key={item.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <p className="font-medium text-sm">{item.name}</p>
                  <p className="text-xs text-gray-500">{item.category}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-mono">${igaPrice?.toFixed(2)}</span>
                    <span className="text-gray-300">vs</span>
                    <span className="font-mono">${twPrice?.toFixed(2)}</span>
                  </div>
                  <Badge variant={igaWins ? "default" : "destructive"} className="text-xs mt-1">
                    {igaWins ? `You save $${Math.abs(diff).toFixed(2)}` : `They're $${Math.abs(diff).toFixed(2)} cheaper`}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Step 4: Margin opportunities**

Create `frontend/src/components/dashboard/margin-opps.tsx`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function MarginOpps({ margins }: { margins: any[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Margin Opportunities</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {(margins || []).map((item: any, idx: number) => (
            <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0 text-sm">
              <div className="flex-1 mr-4">
                <p className="font-medium truncate">{item.name}</p>
              </div>
              <div className="text-right space-x-2">
                <span className="text-gray-500 line-through">${item.tw_price?.toFixed(2)}</span>
                <span className="font-mono">${item.iga_price?.toFixed(2)}</span>
                <span className="text-green-600 font-medium">
                  → ${item.suggested_price?.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

**Verification:** Login, dashboard renders with KPI cards, staple tracker, margin opportunities. All data from API.

---

### Task 7.4: Product search page

**Objective:** Text search + barcode scanner trigger

**Files:**
- Create: `frontend/src/app/search/page.tsx`
- Create: `frontend/src/components/search/search-bar.tsx`
- Create: `frontend/src/components/search/product-card.tsx`

**Step 1: Search page**

Create `frontend/src/app/search/page.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { SearchBar } from "@/components/search/search-bar";
import { ProductCard } from "@/components/search/product-card";
import { Button } from "@/components/ui/button";
import { Camera } from "lucide-react";
import { useRouter } from "next/navigation";

export default function SearchPage() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSearch(query: string) {
    setLoading(true);
    const res = await fetch(`/api/products/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    setResults(data);
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Product Search</h2>
          <p className="text-gray-500 mt-1">Search or scan a barcode</p>
        </div>
        <Button onClick={() => router.push("/scan")} variant="outline">
          <Camera className="h-4 w-4 mr-2" />
          Scan Barcode
        </Button>
      </div>

      <SearchBar onSearch={handleSearch} />
      
      {loading && <p className="text-gray-500">Searching...</p>}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((product: any) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      
      {!loading && results.length === 0 && (
        <p className="text-gray-400 text-center py-12">Search for a product to compare prices</p>
      )}
    </div>
  );
}
```

**Step 2: Search bar component**

Create `frontend/src/components/search/search-bar.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

export function SearchBar({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (query.trim()) onSearch(query.trim());
      }}
      className="flex gap-2"
    >
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search products (e.g. milk, eggs, ground beef)..."
        className="flex-1"
        autoFocus
      />
      <Button type="submit">
        <Search className="h-4 w-4 mr-2" />
        Search
      </Button>
    </form>
  );
}
```

**Step 3: Product card**

Create `frontend/src/components/search/product-card.tsx`:

```tsx
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function ProductCard({ product }: { product: any }) {
  const igaPrice = product.price || product.unit_price;
  const twPrice = product.competitor_price;
  const diff = twPrice ? igaPrice - twPrice : null;
  const igaWins = diff !== null && diff < 0;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <h3 className="font-medium text-sm line-clamp-2 mb-3">{product.name}</h3>
        
        <div className="flex items-center justify-between text-sm">
          <div>
            <p className="text-xs text-gray-500">IGA</p>
            <p className="font-mono font-bold">
              {product.price_display || `$${igaPrice?.toFixed(2)}`}
            </p>
          </div>
          
          {twPrice ? (
            <div>
              <p className="text-xs text-gray-500">Thriftway</p>
              <p className="font-mono font-bold">
                {product.competitor_display || `$${twPrice.toFixed(2)}`}
              </p>
            </div>
          ) : (
            <p className="text-xs text-gray-400">No match</p>
          )}
          
          {diff !== null && (
            <Badge variant={igaWins ? "default" : "destructive"}>
              {igaWins ? "Cheaper" : "Pricier"} ${Math.abs(diff).toFixed(2)}
            </Badge>
          )}
        </div>
        
        {product.match_confidence && (
          <p className="text-xs text-gray-400 mt-2">
            Match: {(product.match_confidence * 100).toFixed(0)}%
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

**Verification:** Navigate to /search, type "milk", see product cards with IGA vs Thriftway prices. Color-coded badges.

---

### Task 7.5: Barcode scanner page

**Objective:** Camera-based barcode scanning with ZXing fallback

**Files:**
- Create: `frontend/src/app/scan/page.tsx`
- Create: `frontend/src/components/scan/barcode-scanner.tsx`

**Step 1: Install ZXing**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm install @zxing/library
```

**Step 2: Barcode scanner component**

Create `frontend/src/components/scan/barcode-scanner.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader } from "@zxing/library";
import { Loader2 } from "lucide-react";

export function BarcodeScanner({ onDetected }: { onDetected: (code: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState("");
  const [scanning, setScanning] = useState(false);
  const [nativeAvailable, setNativeAvailable] = useState(false);

  useEffect(() => {
    // Check for native Barcode Detection API (Chrome/Edge/Samsung)
    if ("BarcodeDetector" in window) {
      setNativeAvailable(true);
      startNativeScanner();
    } else {
      startZxingScanner();
    }

    return () => {
      stopScanner();
    };
  }, []);

  async function startNativeScanner() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setScanning(true);
      
      const detector = new (window as any).BarcodeDetector({
        formats: ["ean_13", "ean_8", "upc_a", "upc_e"],
      });

      const scan = async () => {
        if (!videoRef.current) return;
        try {
          const barcodes = await detector.detect(videoRef.current);
          if (barcodes.length > 0) {
            onDetected(barcodes[0].rawValue);
            return; // Stop after first detection
          }
        } catch (e) {}
        requestAnimationFrame(scan);
      };
      requestAnimationFrame(scan);
    } catch (e) {
      setNativeAvailable(false);
      startZxingScanner(); // Fallback
    }
  }

  let zxingReader: BrowserMultiFormatReader | null = null;

  async function startZxingScanner() {
    try {
      zxingReader = new BrowserMultiFormatReader();
      if (videoRef.current) {
        await zxingReader.decodeFromVideoDevice(
          undefined,
          videoRef.current,
          (result, err) => {
            if (result) {
              onDetected(result.getText());
            }
          }
        );
        setScanning(true);
      }
    } catch (e: any) {
      setError(`Camera error: ${e.message}`);
    }
  }

  function stopScanner() {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((t) => t.stop());
    }
    zxingReader?.reset();
  }

  return (
    <div className="relative">
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}
      <div className="relative bg-black rounded-lg overflow-hidden aspect-[4/3]">
        <video ref={videoRef} className="w-full h-full object-cover" />
        {!scanning && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <Loader2 className="h-8 w-8 text-white animate-spin" />
          </div>
        )}
        <div className="absolute inset-0 border-2 border-white/20 rounded-lg pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-1 bg-red-500/50" />
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        Point camera at a barcode. Works best with good lighting.
        {nativeAvailable && " Using fast native scanner."}
      </p>
    </div>
  );
}
```

**Step 3: Scan page**

Create `frontend/src/app/scan/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { BarcodeScanner } from "@/components/scan/barcode-scanner";
import { ProductCard } from "@/components/search/product-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function ScanPage() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [manualCode, setManualCode] = useState("");
  const router = useRouter();

  async function handleDetected(code: string) {
    setLoading(true);
    const res = await fetch(`/api/products/upc?code=${code}`);
    const data = await res.json();
    setResults(data);
    setLoading(false);
  }

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scan Barcode</h2>
          <p className="text-gray-500 mt-1">Point camera at a UPC barcode</p>
        </div>
      </div>

      <BarcodeScanner onDetected={handleDetected} />
      
      {loading && <p className="text-center text-gray-500">Looking up product...</p>}
      
      {results.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}

      <div className="border-t pt-4">
        <p className="text-sm text-gray-500 mb-2">Or enter code manually:</p>
        <form
          onSubmit={(e) => { e.preventDefault(); handleDetected(manualCode); }}
          className="flex gap-2"
        >
          <Input
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value)}
            placeholder="Enter UPC code..."
          />
          <Button type="submit" disabled={!manualCode.trim()}>Lookup</Button>
        </form>
      </div>
    </div>
  );
}
```

**Verification:** On mobile (or Chrome DevTools mobile emulation), navigate to /scan. Camera activates. Point at a barcode → product results appear. Manual entry also works.

---

### Task 7.6: Department comparison page

**Objective:** Compare IGA vs Thriftway prices by department

**Files:**
- Create: `frontend/src/app/departments/page.tsx`

**Step 1: No new file — just create the page**

No file creation needed — just write the page using existing components.

Create `frontend/src/app/departments/page.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/departments")
      .then((r) => r.json())
      .then(setDepartments)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Department Comparison</h2>
        <p className="text-gray-500 mt-1">How each department stacks up against Thriftway</p>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Department</TableHead>
                  <TableHead className="text-right">Products</TableHead>
                  <TableHead className="text-right">Avg IGA</TableHead>
                  <TableHead className="text-right">Avg Thriftway</TableHead>
                  <TableHead className="text-right">Gap</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {departments.map((dept: any) => {
                  const gap = dept.avg_gap || 0;
                  const igaWins = gap < 0;

                  return (
                    <TableRow key={dept.department_id}>
                      <TableCell className="font-medium">
                        {dept.department_name || `Dept ${dept.department_id}`}
                      </TableCell>
                      <TableCell className="text-right">{dept.product_count}</TableCell>
                      <TableCell className="text-right font-mono">
                        ${dept.avg_iga_price?.toFixed(2) || "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        ${dept.avg_tw_price?.toFixed(2) || "—"}
                      </TableCell>
                      <TableCell className={`text-right font-mono ${igaWins ? "text-green-600" : "text-red-600"}`}>
                        {gap > 0 ? "+" : ""}{gap.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant={igaWins ? "default" : "destructive"}>
                          {igaWins ? "Winning" : "Losing"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

**Verification:** Navigate to /departments — table renders with department names, product counts, average prices, and win/loss badges.

---

### Task 7.7: Margin opportunities page

**Objective:** Full page dedicated to finding where IGA can raise prices

**Files:**
- Create: `frontend/src/app/margins/page.tsx`

**Step 1: No file — just the page**

Create `frontend/src/app/margins/page.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { TrendingUp } from "lucide-react";

export default function MarginsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState(0.05); // Minimum gap

  useEffect(() => {
    fetch(`/api/margins?limit=50`)
      .then((r) => r.json())
      .then((data) => setItems(data.filter((i: any) => i.gap >= filter)));
  }, [filter]);

  const totalOpportunity = items.reduce((sum, i) => sum + (i.gap || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Margin Opportunities</h2>
          <p className="text-gray-500 mt-1">
            Products where you can raise prices and still beat Thriftway
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Total Gap Available</p>
          <p className="text-2xl font-bold text-green-600">${totalOpportunity.toFixed(2)}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">Min gap:</span>
        <Input
          type="number"
          value={filter}
          onChange={(e) => setFilter(parseFloat(e.target.value) || 0)}
          className="w-20"
          step="0.01"
        />
      </div>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">IGA Price</TableHead>
                <TableHead className="text-right">Thriftway</TableHead>
                <TableHead className="text-right">Gap</TableHead>
                <TableHead className="text-right">Suggested</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item: any, idx: number) => (
                <TableRow key={idx}>
                  <TableCell className="font-medium max-w-xs truncate">
                    {item.name}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    ${item.iga_price?.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-gray-500">
                    ${item.tw_price?.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-green-600">
                    ${(item.gap || 0).toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-mono font-bold">
                    ${item.suggested_price?.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge className="bg-green-100 text-green-700">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      Raise
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Verification:** Navigate to /margins — table shows products sorted by gap. Shows suggested price. Total opportunity dollar amount at top.

---

### Task 7.8: Reports page (placeholder)

**Objective:** Simple reports page with CSV export capability

**Files:**
- Create: `frontend/src/app/reports/page.tsx`

**Step 1: Write reports page**

Create `frontend/src/app/reports/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, FileText, TrendingUp, AlertTriangle } from "lucide-react";

export default function ReportsPage() {
  const [exporting, setExporting] = useState(false);

  async function exportCSV(type: string) {
    setExporting(true);
    let url = "";
    if (type === "staples") url = "/api/staples";
    else if (type === "margins") url = "/api/margins?limit=100";
    else if (type === "departments") url = "/api/departments";
    
    const res = await fetch(url);
    const data = await res.json();
    
    const csv = data.length
      ? [Object.keys(data[0]).join(","), ...data.map((row: any) => Object.values(row).join(","))].join("\n")
      : "No data";

    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `grocery-store-wars-${type}-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    setExporting(false);
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
        <p className="text-gray-500 mt-1">Export pricing data and analysis</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Staple Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">
              Current prices for all tracked staple items with IGA vs Thriftway comparison.
            </p>
            <Button onClick={() => exportCSV("staples")} disabled={exporting} variant="outline" className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Margin Opportunities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">
              Top 100 products where IGA can raise prices and still beat Thriftway.
            </p>
            <Button onClick={() => exportCSV("margins")} disabled={exporting} variant="outline" className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Department Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">
              Department-level comparison showing which categories need attention.
            </p>
            <Button onClick={() => exportCSV("departments")} disabled={exporting} variant="outline" className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Weekly Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            Automated weekly email reports with price changes, new margin opportunities, 
            and department-level trends. Coming in v2.
          </p>
          <Badge variant="secondary" className="mt-2">Coming Soon</Badge>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Verification:** Navigate to /reports — three export cards. Click Export CSV → downloads file with real data.

---

### Task 7.9: Settings page

**Objective:** Staple item management, manual match override, data freshness display

**Files:**
- Create: `frontend/src/app/settings/page.tsx`

**Step 1: Write settings page**

Create `frontend/src/app/settings/page.tsx`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import turso from "@/db";

export default async function SettingsPage() {
  // Get data freshness
  const stores = await turso.execute("SELECT * FROM stores");
  const matchCounts = await turso.execute(
    "SELECT match_type, COUNT(*) as cnt FROM product_matches GROUP BY match_type"
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-gray-500 mt-1">Data health and configuration</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Data Freshness</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stores.rows.map((store: any) => (
              <div key={store.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <p className="font-medium">{store.name}</p>
                  <p className="text-xs text-gray-500">{store.product_count?.toLocaleString()} products</p>
                </div>
                <div className="text-right">
                  <p className="text-sm">
                    Last scraped: {store.last_scraped_at || "Never"}
                  </p>
                  <Badge variant={store.active ? "default" : "secondary"}>
                    {store.active ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Product Matching</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {matchCounts.rows.map((row: any) => (
              <div key={row.match_type} className="flex justify-between text-sm">
                <span className="capitalize">{row.match_type?.replace("_", " ")}</span>
                <span className="font-mono">{row.cnt?.toLocaleString()} matches</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-4">
            Manual match override coming in v2. Contact support for match corrections.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Scraping Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>IGA Freshop (full refresh)</span>
              <Badge>Nightly, 2am</Badge>
            </div>
            <div className="flex justify-between">
              <span>Mercato staple check</span>
              <Badge>Weekly, Mon 3am</Badge>
            </div>
            <div className="flex justify-between">
              <span>Product matching</span>
              <Badge>After each scrape</Badge>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-4">
            Schedule managed via GitHub Actions. Edit workflows to adjust timing.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Verification:** Navigate to /settings — shows data freshness for both stores, match stats, scraping schedule.

---

## PHASE 8: Cloud Deployment (Day 12-13)

### Task 8.1: Deploy to Vercel (free tier)

**Objective:** Frontend live on Vercel with Turso connection

**Files:**
- Create: `frontend/vercel.json`

**Step 1: Create vercel.json**

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

**Step 2: Link and deploy**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npx vercel login
npx vercel link
npx vercel --prod
```

**Step 3: Set environment variables on Vercel**

In Vercel dashboard:
- `TURSO_DATABASE_URL` = your Turso URL
- `TURSO_AUTH_TOKEN` = your Turso token
- `NEXTAUTH_SECRET` = generated secret
- `NEXTAUTH_URL` = your Vercel deployment URL

**Verification:** Visit deployed URL — login page renders. Login works. Dashboard loads data from Turso.

---

### Task 8.2: Set up GitHub Actions for nightly scrapers

**Objective:** Automatic nightly IGA scrape + weekly Mercato check via GitHub Actions (free tier includes 2,000 min/month)

**Files:**
- Create: `.github/workflows/scrape-iga.yml`
- Create: `.github/workflows/scrape-thriftway.yml`

**Step 1: Nightly IGA scraper workflow**

Create `.github/workflows/scrape-iga.yml`:

```yaml
name: Scrape IGA Prices (Nightly)

on:
  schedule:
    - cron: '0 9 * * *'  # 2am PST = 9am UTC
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd scrapers
          pip install httpx python-dotenv libsql-client
      
      - name: Run IGA scraper
        env:
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
        run: |
          cd scrapers
          python -c "
          from scrapers.iga import scrape_products
          scrape_products(batch_size=100, delay=1.0)
          from scrapers.matcher import match_all
          match_all()
          "
```

**Step 2: Weekly Mercato check workflow**

Create `.github/workflows/scrape-thriftway.yml`:

```yaml
name: Scrape Thriftway Prices (Weekly)

on:
  schedule:
    - cron: '0 10 * * 1'  # 3am PST Monday = 10am UTC Monday
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd scrapers
          pip install httpx python-dotenv libsql-client thefuzz python-Levenshtein
      
      - name: Run price updater (targeted staple check)
        env:
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
        run: |
          cd scrapers
          echo "Price update from scheduled check (use mercato.py manually for full staple scrape)"
          # See Task 3.1 note — Mercato blocking in CI likely, manual run on MacBook instead
      
      - name: Re-run matcher
        env:
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
        run: |
          cd scrapers
          python -c "from scrapers.matcher import match_all; match_all()"
```

**Step 3: Set GitHub Actions secrets**

In repo → Settings → Secrets and variables → Actions:
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

**Verification:** Trigger workflow manually from Actions tab. Confirms IGA scrape completes and data appears in dashboard.

**Note on Mercato scraping (#3 constraint):** Due to zero monthly spend, Mercato browser scraping runs from John's MacBook manually — once weekly, the staple scraper (`mercato.py`) runs locally and pushes updated prices. Cloudflare anti-bot on GitHub Actions runners makes CI-based Mercato scraping impractical without a residential proxy.

---

## PHASE 9: Polish & QA (Day 13-14)

### Task 9.1: Responsive design pass

**Objective:** Mobile-friendly sidebar, touch targets, readable on phone

**Files:**
- Modify: `frontend/src/components/nav.tsx`
- Modify: `frontend/src/app/layout.tsx`

**Step 1: Make nav collapsible on mobile**

Add to `nav.tsx` a mobile hamburger:

```tsx
"use client";

// Add at top of component:
const [open, setOpen] = useState(false);

// Wrap nav in:
<>
  <Button variant="ghost" className="lg:hidden fixed top-4 left-4 z-50" onClick={() => setOpen(!open)}>
    <Menu className="h-5 w-5" />
  </Button>
  
  {open && (
    <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setOpen(false)} />
  )}
  
  <nav className={cn(
    "fixed lg:static inset-y-0 left-0 z-40 w-64 border-r bg-white p-4 space-y-1 transform transition-transform lg:transform-none",
    open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
  )}>
    {/* existing nav content */}
  </nav>
</>
```

**Step 2: Test on mobile viewport**

In Chrome DevTools: toggle device toolbar, test iPhone 14 Pro, Pixel 7, iPad.

**Verification:** All pages readable on mobile. Sidebar collapses to hamburger. Touch targets >= 44px. Tables scroll horizontally.

---

### Task 9.2: Error states and loading states

**Objective:** Graceful handling of API failures, empty states, loading spinners

**Files:**
- Modify: all pages with data fetching

Each page needs:
- Loading state: spinner or skeleton
- Empty state: "No data yet. Scrapers may still be running."
- Error state: "Failed to load data. Please try again."

Example pattern:

```tsx
if (loading) return <Skeleton className="h-64 w-full" />;
if (error) return <div className="text-red-500">Failed to load: {error}</div>;
if (!data?.length) return <div className="text-gray-400">No data yet</div>;
```

**Verification:** Block Turso in browser DevTools → pages show error states gracefully. Load pages with empty DB → show empty states.

---

### Task 9.3: Final QA checklist

**Objective:** End-to-end verification

Manual checks:
- [ ] Login works with seeded admin user
- [ ] Dashboard loads KPI cards with real numbers
- [ ] Staple tracker shows milk, eggs, etc with IGA vs Thriftway prices
- [ ] Margin opportunities table shows products with green "raise" badges
- [ ] Product search: type "milk" → results appear with price comparison
- [ ] Product search: click "Scan Barcode" → camera opens (on mobile)
- [ ] Department comparison: table shows departments with win/loss badges
- [ ] Reports: CSV export downloads real data
- [ ] Settings: shows data freshness and match statistics
- [ ] Mobile: sidebar collapses, tables scroll, touch targets work
- [ ] Error: disconnect network → error states show, not crashes
- [ ] Empty: fresh DB → empty states show, not crashes
- [ ] Cron: GitHub Actions workflow runs and updates data

---

## Summary: What Gets Built (MVP)

By end of Phase 9, the MVP delivers:

1. **Dashboard** — KPI cards (product counts, price gap), staple price watch, top margin opportunities
2. **Product Search** — text search with autocomplete, side-by-side IGA vs Thriftway comparison
3. **Barcode Scanner** — camera-based UPC scanning (native API on Chrome, ZXing fallback on Safari)
4. **Department Comparison** — sortable table of departments with avg prices and win/loss
5. **Margin Opportunities** — full page of products where IGA can raise prices
6. **Reports** — CSV export for staples, margins, departments
7. **Settings** — data freshness monitoring, match statistics
8. **Auth** — single admin user login
9. **Nightly Scrapers** — GitHub Actions (IGA auto) + manual Mercato run from MacBook

---

## What's Deferred to V2

- Shelf-tag photo upload (Thriftway price verification)
- Multi-store support (white-label for other grocers)
- AI price optimization suggestions
- Email reports
- Push notifications for price alerts
- Weekly ad intelligence
- Sales velocity scoring
- Manual product match override UI
- POS system integration

---

## Cost Summary

| Service | Plan | Monthly |
|---------|------|---------|
| Vercel | Hobby | $0 |
| Turso | Free (9GB, 1B reads) | $0 |
| GitHub Actions | Free (2,000 min) | $0 |
| **Total** | | **$0** |

---

## Post-MVP: What to Focus On

After MVP ships and IGA owner uses it:

1. **Get Thriftway pricing current** — the shelf-tag photo upload (V2) or weekly in-store price checks are the single biggest value driver. Without current Thriftway prices, margin opportunities are speculative.
2. **Train the IGA owner** — they need to understand the margin opportunity finder. One 30-minute session where you spot 5 products they can raise prices on = instant ROI proof.
3. **Build the sales deck** — if this is John's product to sell, package the dashboard into a sellable unit: demo video, pricing sheet, ROI calculator, onboarding docs.
4. **White-label it** — remove IGA/Thriftway hardcoding. Store config becomes data-driven. Add store setup wizard.

---

**Plan complete.** Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review. Shall I proceed?
