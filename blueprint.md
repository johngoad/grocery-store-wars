# Vashon Price Wars — Full Blueprint

**Date:** May 17, 2026
**Author:** Herman
**Status:** Awaiting John's Approval

---

## 1. EXECUTIVE SUMMARY

Two grocery stores. One island. One tool that gives IGA the power to see exactly where they're winning, where they're bleeding, and where they can quietly raise prices.

We build a dashboard that scrapes both stores' online pricing, matches products across stores, and shows the IGA owner a live competitive intelligence feed. The app includes UPC barcode scanning from a phone camera and text search for on-the-floor price checks.

The core technical discovery: both stores use the **same e-commerce platform** (Freshop by NCR), making the data pipeline dramatically simpler than originally anticipated. The catch: Thriftway abandoned their Freshop store in 2020 and moved active pricing to Mercato.

---

## 2. DATA LANDSCAPE

### IGA — Vashon Market Fresh
| Attribute | Value |
|-----------|-------|
| Platform | Freshop by NCR |
| API Base | `https://api.freshop.ncrcloud.com/` |
| App Key | `vashon_fresh_market` |
| Store ID | `7432` |
| Product Count | 12,018 |
| Data Freshness | **Current** (last update: May 12, 2026) |
| Auth Required | None (open reads) |
| Product Fields | name, price, unit_price, upc, department_ids, brand, manufacturer, size, nutrition, images, barcode (UPC-A, EAN-13, EAN-8) |
| Image CDN | `https://images.freshop.ncrcloud.com/` |
| Pickup/Delivery | Yes (pickup $4.95, delivery $8.95) |

### Thriftway — Vashon Thriftway
| Attribute | Value |
|-----------|-------|
| Platform (stale) | Freshop by NCR |
| Freshop Store ID | `1813` |
| Freshop App Key | `vashon_thriftway` |
| Freshop Product Count | 70,990 |
| Freshop Data Freshness | **Stale** (last update: March 2020 — 6+ years old) |
| Platform (active) | Mercato |
| Mercato Product Count | 15,181 |
| Mercato Data Freshness | **Current** (live active orders) |
| Mercato Auth | Unknown (Next.js client-side, API not publicly accessible) |
| Pickup/Delivery | Yes via Mercato |

### Critical Insight
Both stores are on the SAME Freshop platform. The IGA store data is actively maintained. Thriftway abandoned Freshop in favor of Mercato. This creates a dual-source data problem:

- **IGA**: One clean API (Freshop)
- **Thriftway**: Two data sources — stale Freshop (70K products, complete catalog, bad prices) + live Mercato (15K products, good prices, incomplete catalog)

### Freshop API Endpoints Discovered
```
GET /stores?app_key=vashon_fresh_market
  → Returns store list with IDs, metadata, fulfillment config

GET /products?app_key=vashon_fresh_market&store_id=7432&limit=100&offset=0
  → Paginated product list with prices, UPCs, departments

GET /products?app_key=vashon_fresh_market&store_id=7432&q=milk
  → Full-text search (326 results for "milk")

GET /products?app_key=vashon_fresh_market&store_id=7432&department_ids=22873310
  → Filter by department (22873310 = Meat)

GET /departments?app_key=vashon_fresh_market&store_id=7432
  → 1,341 departments/shelves with hierarchy

GET /products/:id?app_key=vashon_fresh_market&store_id=7432
  → Single product detail with nutrition, images, varieties
```

Sample IGA product (Food Club Milk, Whole 1 Gal):
```json
{
  "id": "577599",
  "name": "Food Club Milk, Whole 1 Gal",
  "price": "$3.89",
  "unit_price": 3.89,
  "upc": "3680097630",
  "category": "DAIRY",
  "brand": "Food Club",
  "manufacturer": "Topco Assoc LLC",
  "size": "1 gal",
  "barcode": "036800976306",
  "barcode_upc_a": "036800976306",
  "barcode_ean13": "0036800976306",
  "last_updated_at": "2026-03-08T19:03:54.000+00:00",
  "canonical_url": "https://shop.vashonmarket.com/shop/food_club_milk_whole_1_gal/p/577599",
  "images": [{"identifier": "00036800976306/9ca7e4c62bd...", "sequence": 0}]
}
```

### Mercato Scraping Strategy
Mercato's API is not publicly documented and appears to use Next.js with client-side rendering. The scraping approach for Thriftway will be:

**Primary Approach: Browser Automation (Puppeteer)**
- Navigate Mercato store page, iterate departments
- Extract product names, prices, sizes from rendered DOM
- 15,181 products ÷ 30 products per page = ~507 pages
- Human-like delays (5-15 seconds between pages, randomized)
- Rotate user agents, viewport sizes, scroll behavior
- Residential proxy recommended to avoid Mercato rate limiting
- Estimated time: 8-12 hours for full scrape (spread over 2-3 days)

**Fallback: Freshop Stale Data with Price Override**
- Use Thriftway's Freshop data (70K products) for catalog completeness
- Overlay Mercato prices where available (fuzzy name matching)
- Flag products where Thriftway Freshop price diverges from Mercato
- Only scrape Mercato for high-priority products (staples, top sellers)

### Product Matching Strategy
Since UPC codes exist in Freshop but may not be in Mercato's rendered output:

1. **Exact UPC match** — when both sources have 12-digit UPCs
2. **Fuzzy name + size match** — normalize names (lowercase, remove brand suffixes, trim), compare with Levenshtein distance < 5
3. **Manual mapping override** — admin can link products that automated matching misses
4. **Confidence score** — 0-100% displayed on each match, low-confidence matches flagged for review

---

## 3. PRODUCT VISION

### What It Is
A competitive intelligence dashboard for independent grocers. Shows the IGA owner:
- Where they're cheaper than Thriftway (winning)
- Where they're more expensive (losing business)
- Where they're close but could raise prices and still be cheaper (pure margin opportunity)
- Department-level comparison (Meat vs Meat, Produce vs Produce)
- KPI dashboard tracking staple items (milk, eggs, ground beef, bread, mayonnaise)

### What It Is NOT
- Not a consumer shopping comparison app
- Not a public website (password-protected, white-label)
- Not real-time (data refreshed nightly, not live)

### Core Use Cases
1. **Floor Price Check** — IGA employee scans a UPC or searches a product on their phone to see the Thriftway price instantly
2. **Department Audit** — Manager reviews all Meat department prices side-by-side, adjusts where needed
3. **Margin Opportunity Finder** — Dashboard highlights "IGA is $2.99, Thriftway is $3.79 — raise to $3.49 and still win"
4. **Staple KPI Monitor** — Dashboard shows trending prices for milk, eggs, ground beef, bread, mayo
5. **Weekly Ad Intelligence** — IGA sees what Thriftway has on sale before planning their own weekly ad

---

## 4. TECHNICAL ARCHITECTURE

### Stack
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 15 (App Router) | Fast, SEO-friendly, Vercel deployable |
| Styling | Tailwind CSS + shadcn/ui | Clean, accessible, component library |
| Charts | Tremor or Recharts | Dashboard KPIs and comparison charts |
| API Layer | Next.js API Routes + FastAPI (scrapers) | Next.js handles dashboard API, FastAPI handles scraping |
| Database | SQLite (MVP) → PostgreSQL (scale) | Simple, zero-config for MVP |
| Scrapers | Python + Puppeteer (Node.js) | Python for Freshop API, Puppeteer for Mercato browser automation |
| Auth | NextAuth.js | Simple email/password for admin |
| Hosting | Vercel (frontend) + Hetzner VPS (scrapers) | Vercel free tier for dashboard, $5/mo VPS for scrapers |
| Image CDN | Freshop CDN (existing) | Product images already hosted |

### System Diagram
```
┌─────────────────────────────────────────────────────────┐
│                     Vercel (Frontend)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Dashboard │  │ Barcode  │  │ Product Comparison   │  │
│  │ (KPI/Charts)│ │ Scanner  │  │ (Side-by-side)      │  │
│  └─────┬────┘  └────┬─────┘  └──────────┬───────────┘  │
│        │            │                    │               │
│        └────────────┼────────────────────┘               │
│                     │                                    │
│              ┌──────▼──────┐                             │
│              │  API Routes │                             │
│              │  (Next.js)  │                             │
│              └──────┬──────┘                             │
└─────────────────────┼────────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │   SQLite DB    │
              │  (Products,    │
              │   Prices,      │
              │   Matches,     │
              │   History)     │
              └───────┬────────┘
                      │
┌─────────────────────┼────────────────────────────────────┐
│            Hetzner VPS (Scrapers)                        │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │              FastAPI Scraper Service              │   │
│  │                                                   │   │
│  │  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │ Freshop API   │  │  Mercato Browser          │  │   │
│  │  │ Scraper       │  │  Scraper (Puppeteer)     │  │   │
│  │  │ (IGA prices)  │  │  (Thriftway prices)      │  │   │
│  │  └──────────────┘  └──────────────────────────┘  │   │
│  │                                                   │   │
│  │  ┌──────────────────────────────────────────────┐│   │
│  │  │  Product Matcher (fuzzy name + UPC matching) ││   │
│  │  └──────────────────────────────────────────────┘│   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Schedule: cron (nightly 2am-6am PST)                   │
│  Human behavior: 5-15s delays, rotating UA, residential │
│                  proxy for Mercato scraping              │
└──────────────────────────────────────────────────────────┘
```

### Database Schema (SQLite)
```sql
-- Stores
CREATE TABLE stores (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,  -- 'freshop' or 'mercato'
    api_key TEXT,
    store_id TEXT,
    base_url TEXT,
    last_scraped_at TIMESTAMP,
    product_count INTEGER,
    active BOOLEAN DEFAULT 1
);

-- Departments
CREATE TABLE departments (
    id TEXT PRIMARY KEY,
    store_id TEXT REFERENCES stores(id),
    name TEXT NOT NULL,
    parent_id TEXT,
    product_count INTEGER
);

-- Products
CREATE TABLE products (
    id TEXT PRIMARY KEY,  -- store_id + upc where available, otherwise store_id + slug
    store_id TEXT REFERENCES stores(id),
    name TEXT NOT NULL,
    price REAL NOT NULL,
    unit_price REAL,
    price_display TEXT,  -- "$3.89"
    upc TEXT,
    barcode TEXT,
    barcode_type TEXT,  -- 'UPC-A', 'EAN-13', 'EAN-8', 'PLU'
    size TEXT,  -- "1 gal", "6.4 oz", "lb"
    brand TEXT,
    manufacturer TEXT,
    department_id TEXT,
    category TEXT,
    image_url TEXT,
    product_url TEXT,
    is_weight_required BOOLEAN DEFAULT 0,
    quantity_label TEXT,
    last_updated_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price History (for trend tracking)
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT REFERENCES products(id),
    store_id TEXT REFERENCES stores(id),
    price REAL NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product Matches
CREATE TABLE product_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iga_product_id TEXT REFERENCES products(id),
    thriftway_product_id TEXT REFERENCES products(id),
    match_type TEXT,  -- 'upc_exact', 'fuzzy_name', 'manual'
    confidence REAL,  -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staple Items (for KPI dashboard)
CREATE TABLE staple_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    iga_product_id TEXT REFERENCES products(id),
    thriftway_product_id TEXT REFERENCES products(id),
    category TEXT,  -- 'dairy', 'meat', 'produce', 'pantry'
    display_order INTEGER
);

-- Scan History
CREATE TABLE scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upc TEXT,
    product_name TEXT,
    iga_price REAL,
    thriftway_price REAL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. SCRAPING ARCHITECTURE — DETAILED

### IGA Scraper (Freshop API — Easy)
```python
# Pseudocode
class IGAFreshopScraper:
    BASE_URL = "https://api.freshop.ncrcloud.com"
    APP_KEY = "vashon_fresh_market"
    STORE_ID = "7432"

    def scrape_all(self):
        # 1. Get all departments
        depts = self.fetch("/departments")

        # 2. Paginate through all products
        offset = 0
        limit = 100
        while True:
            products = self.fetch(
                f"/products?store_id={self.STORE_ID}&limit={limit}&offset={offset}"
            )
            if not products['items']:
                break
            self.save_products(products['items'])
            offset += limit

        # 3. For each product, get full detail (nutrition, varieties)
        for product in self.get_all_products():
            detail = self.fetch(f"/products/{product['id']}")
            self.update_product_detail(product['id'], detail)

    def fetch(self, path, params=None):
        url = f"{self.BASE_URL}{path}"
        if '?' not in url:
            url += f"?app_key={self.APP_KEY}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
```

**Rate Limits:** None observed. 12,018 products at 100/request = ~121 requests. Add full detail fetch = ~12,118 more. Total ~12,239 requests. At 1 request/second with 2s delay = ~7 hours for full initial scrape. Subsequent scrapes only fetch changed products (check `last_updated_at`).

### Thriftway Scraper (Mercato Browser Automation — Complex)

**Strategy: Hybrid Approach**

Phase 1 — Use Freshop Stale Data for Catalog
- Pull all 70,990 Thriftway products from Freshop API
- These have complete metadata (UPCs, brands, sizes, departments)
- Mark all prices as "stale" and flag for Mercato verification

Phase 2 — Mercato Price Extraction
- Use Puppeteer to browse Mercato Thriftway store
- Navigate through departments, extract product names and prices
- Match extracted prices back to Freshop catalog via fuzzy name matching
- Update prices in database, mark as verified

Phase 3 — Continuous Monitoring
- Nightly: re-scrape Mercato for price changes on tracked products
- Weekly: full Mercato department crawl
- Flag products with price changes > 10%

```javascript
// Puppeteer scraping pseudocode
const mercatoScraper = {
  baseUrl: 'https://www.mercato.com/shop/vashon-thriftway',

  async scrapeAll() {
    await this.setZipCode('98070'); // Required by Mercato

    const departments = [
      'fruits-veggies', 'meat', 'dairy-refrigerated',
      'pantry', 'frozen-foods', 'beverages'
    ];

    for (const dept of departments) {
      await this.scrapeDepartment(dept);
    }
  },

  async scrapeDepartment(dept) {
    await page.goto(`${this.baseUrl}/${dept}`, {
      waitUntil: 'networkidle2'
    });

    // Human-like scroll behavior
    await this.humanScroll();

    // Extract products from rendered DOM
    const products = await page.evaluate(() => {
      return [...document.querySelectorAll('[data-testid="product-card"]')]
        .map(card => ({
          name: card.querySelector('[data-testid="product-name"]')?.textContent,
          price: card.querySelector('[data-testid="product-price"]')?.textContent,
          size: card.querySelector('[data-testid="product-size"]')?.textContent,
        }));
    });

    await this.saveWithDelay(products);
  },

  async humanScroll() {
    const delay = () => 5000 + Math.random() * 10000; // 5-15 seconds
    await page.evaluate(async () => {
      await new Promise(resolve => {
        let totalHeight = 0;
        const distance = 100;
        const timer = setInterval(() => {
          window.scrollBy(0, distance);
          totalHeight += distance;
          if (totalHeight >= document.body.scrollHeight) {
            clearInterval(timer);
            resolve();
          }
        }, 200);
      });
    });
    await page.waitForTimeout(delay());
  },

  async saveWithDelay(products) {
    for (const product of products) {
      await db.insert('mercarto_products', product);
      await page.waitForTimeout(2000 + Math.random() * 3000);
    }
  }
};
```

**Human Behavior Simulation:**
- Random delays: 5-15 seconds between page loads
- 30-60 seconds between department changes
- Scroll speed varies per page
- Viewport sizes rotate (desktop → tablet → desktop)
- User agent rotates from a pool of 10 Chrome/Firefox/Safari strings
- Session cookie maintained across scrape (appears as returning customer)
- Residential proxy ($30-50/month) to avoid data center IP blocks
- Only scrape 2-4 hours per night (2am-6am PST)
- Spread full catalog scrape over 7-10 days

### Scraping Schedule
```
┌──────────┬─────────────────────────────────────┐
│ Schedule │               Task                    │
├──────────┼─────────────────────────────────────┤
│ Nightly  │ IGA Freshop full product refresh     │
│ 2am PST  │ (API calls, 30-60 min)                │
├──────────┼─────────────────────────────────────┤
│ Nightly  │ Mercato staple/tracked items check    │
│ 3am PST  │ (Browser, 1-2 hours)                  │
├──────────┼─────────────────────────────────────┤
│ Weekly   │ Mercato department crawl (one dept)   │
│ Mon 3am  │ Rotating: Meat → Dairy → Produce...   │
├──────────┼─────────────────────────────────────┤
│ Monthly  │ Full Mercato catalog re-scrape         │
│ 1st Sun  │ (Browser, spread over 7-10 nights)    │
└──────────┴─────────────────────────────────────┘
```

---

## 6. FRONTEND — PAGES & COMPONENTS

### Page 1: Login
- Simple email/password
- "Vashon Market Fresh" branding (white label)
- Remember me checkbox

### Page 2: Dashboard (Home)
```
┌──────────────────────────────────────────────────────────┐
│  Vashon Price Wars                          [Settings ⚙] │
│  Last updated: May 17, 2026 3:47 AM                       │
├───────────┬───────────┬───────────┬──────────────────────┤
│  IGA      │ Thriftway │ Price Gap │ Products Compared    │
│  Savings  │ Higher    │ Avg       │                      │
│  ─────    │ ─────     │ ─────     │ 12,018 vs 15,181     │
│  34%      │ 52%       │ $0.87     │ 8,243 matched        │
│  cheaper  │ pricier   │           │                      │
├───────────┴───────────┴───────────┴──────────────────────┤
│                                                          │
│  PRICE TREND — STAPLE ITEMS (30-day)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Milk (1 gal)  │  Eggs (12 ct) │  Ground Beef    │   │
│  │  IGA: $3.89 ▲  │  IGA: $4.29 ▼ │  IGA: $5.99 ▲  │   │
│  │  TW:  $4.49 →  │  TW:  $5.99 → │  TW:  $6.49 →  │   │
│  │  YOU WIN $0.60 │  YOU WIN $1.70│  YOU WIN $0.50  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  DEPARTMENT COMPARISON                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Meat Dept        ████████████░░░░  +12% IGA     │   │
│  │  Dairy Dept       ██████░░░░░░░░░░  -22% IGA     │   │
│  │  Produce Dept     ████████░░░░░░░░  -8% IGA      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  TOP MARGIN OPPORTUNITIES                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Product              IGA     TW     Raise To    │   │
│  │  ────────             ───     ──     ────────    │   │
│  │  Ground Beef 80/20    $5.99   $6.49  $6.29       │   │
│  │  Sourdough Bread      $3.49   $4.99  $4.49       │   │
│  │  Hellmann's Mayo 30oz $4.99   $6.79  $5.99       │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Page 3: Product Search
- Search bar with autocomplete
- Barcode scanner button (opens camera on mobile)
- Results show side-by-side prices
- Color-coded: green = IGA cheaper, red = Thriftway cheaper
- Filter by department, brand, category

### Page 4: Department Comparison
- Select department (Meat, Dairy, Produce, Deli, Bakery, etc.)
- Sortable table: Product Name | IGA Price | Thriftway Price | Difference | % Gap
- Visual indicators for winning/losing
- Bulk export to CSV

### Page 5: Product Detail
- Full product information from both stores
- Price history chart (30/60/90 day)
- Nutrition info (from Freshop API)
- Product images
- Match confidence indicator

### Page 6: Reports
- Weekly price change summary
- Department-level reports
- Staple item trend reports
- Exportable PDF/CSV

### Page 7: Settings
- Scraping schedule configuration
- Manual product match override
- Staple item selection
- Data freshness monitoring

---

## 7. MOBILE EXPERIENCE

### Barcode Scanner (Phone Camera)
- Uses browser Barcode Detection API (Chrome, Edge, Samsung Internet)
- Falls back to ZXing library for Safari/Firefox
- Real-time scanning — point camera at UPC, auto-detect
- Instant price comparison result
- Works offline for previously scanned products

### Progressive Web App (PWA)
- Installable on phone home screen
- Offline mode for cached product data
- Push notifications for price alerts (future)

---

## 8. IMPLEMENTATION PLAN

### Phase 1: Data Pipeline (Week 1-2)
- [ ] Set up project structure (monorepo: frontend/ + scrapers/)
- [ ] Build SQLite database and migrations
- [ ] Build IGA Freshop API scraper
- [ ] Build Thriftway Freshop API scraper (stale data for catalog)
- [ ] Build Mercato browser scraper (Puppeteer)
- [ ] Build product matching engine (UPC + fuzzy name)
- [ ] Set up cron scheduling for scrapers
- [ ] Initial full scrape of both stores
- [ ] Verify data quality (spot-check prices in-store if possible)

### Phase 2: Dashboard Frontend (Week 2-3)
- [ ] Next.js project with Tailwind + shadcn/ui
- [ ] Database connection layer (Prisma)
- [ ] Authentication (NextAuth.js)
- [ ] Dashboard page with KPI cards
- [ ] Staple items chart (Tremor/Recharts)
- [ ] Department comparison view
- [ ] Margin opportunity finder
- [ ] Product search with autocomplete

### Phase 3: Mobile & Scanner (Week 3)
- [ ] Responsive mobile design pass
- [ ] Barcode scanner integration (Barcode Detection API + ZXing fallback)
- [ ] PWA manifest and service worker
- [ ] Offline product cache

### Phase 4: Reports & Polish (Week 4)
- [ ] Weekly report generation
- [ ] Price history charts
- [ ] CSV/PDF export
- [ ] Admin settings page
- [ ] Manual product match override UI
- [ ] Final QA and bug fixes

---

## 9. MONETIZATION & SALES STRATEGY

### Pricing Model
| Tier | Price | Features |
|------|-------|----------|
| Setup Fee | $2,500 one-time | Initial data scrape, brand customization, onboarding, training |
| Monthly | $199/month | Nightly price updates, dashboard access, reports, support |
| Annual | $1,990/year (2 months free) | Same as monthly |

### Sales Pitch to IGA Owner
"Every week, you're leaving money on the table. I can tell you exactly which products, exactly how much, and exactly what price to set. The tool pays for itself in the first month."

Key talking points:
- "One price adjustment of $0.30 on a product you sell 50x/week = $780/year"
- "Find 10 of those opportunities and the tool generates $7,800/year in pure margin"
- "Know what Thriftway charges before you set your weekly ad prices"
- "Your employees can price-check Thriftway from the floor with their phone"
- "White-label — looks like your own internal tool"

### Upsell Path
- Month 1-3: Prove ROI with margin reports
- Month 4: Offer competitor analysis for other stores in their IGA network
- Month 6: Offer white-labeled version to other independent grocers (recurring revenue)

---

## 10. KNOWN RISKS & MITIGATIONS

| Risk | Severity | Mitigation |
|------|----------|------------|
| Mercato blocks scraping IP | High | Residential proxy + human-like delays + spread over 7-10 days |
| Mercato changes DOM structure | Medium | Monitor scrape health, alert on >20% product match failure |
| Thriftway Freshop data too stale for matching | Medium | Prioritize Mercato-scraped names for matching engine |
| Freshop API changes/rate limits | Low | API is stable since 2016, cache aggressively |
| Product matching false positives | Medium | Confidence score display, manual override UI, human review queue |
| IGA owner doesn't maintain their Freshop prices | High | System monitors last_updated_at, alerts when data goes stale |
| Mercato stops serving Thriftway | Low | Fall back to Freshop stale data with "unverified" flag |
| Legal concerns (scraping TOS) | Low | Public data, non-commercial use of scraped content for comparison only |

---

## 11. FUTURE ENHANCEMENTS (v2+)

- Price alert push notifications (price drops, competitor changes)
- AI price optimization (suggest optimal price based on elasticity)
- Multi-store support (white-label for other independent grocers)
- Weekly ad intelligence (scan competitor circular)
- Sales velocity estimates (popularity score from Freshop API)
- Integration with IGA POS system for inventory-aware pricing
- Historical price gap trending (is IGA gaining or losing ground?)
- Consumer-facing "shop local savings" widget

---

## 12. OPEN QUESTIONS FOR JOHN

1. **Relationship:** Do you already have a relationship with the IGA owner, or are we building this on spec to sell?

2. **IGA Data Maintenance:** Will the IGA owner actively maintain their Freshop product catalog and pricing, or is this something we need to help them with? The system only works if IGA's own prices are current.

3. **Mercato Scraping Budget:** The Mercato browser automation requires a residential proxy ($30-50/month) and a VPS ($5-15/month). Acceptable?

4. **Data Source Strategy:** I propose using Thriftway's stale Freshop data (70K products) for the product catalog/metadata and Mercato (15K) for current pricing. This gives us the best of both worlds — complete product matching plus current prices. Does this approach work for you?

5. **Timeline:** 4-week MVP acceptable?

6. **App Name:** "Vashon Price Wars" — too aggressive for an island grocery store that prides itself on community? Alternatives: "Market View", "Vashon Price Compass", "IGA Competitive Intelligence". The current name has personality but the owner might prefer something more professional.

7. **Phone Camera UPC Scanning:** Uses the browser's built-in Barcode Detection API. Works great on Chrome/Edge/Samsung. Falls back to ZXing library for Safari. This covers ~95% of phones. Acceptable?

---

## 13. NEXT STEPS

1. John reviews and approves this blueprint
2. I write the bite-sized implementation plan (tasks with file paths)
3. We start coding Phase 1: Data Pipeline
