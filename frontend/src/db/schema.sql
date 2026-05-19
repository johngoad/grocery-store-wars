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
