# GSW Dashboard & Product Matching v2 Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a beautiful, IGA-focused competitive intelligence dashboard with dynamic data, beautiful graphs, and AI-assisted cross-store product matching.

**Architecture:** Next.js 15 + shadcn/ui + Tailwind + recharts (already installed). Data flows from Turso HTTP API through API routes to React components. Product matching uses local fuzzy engine (v5) with LLM fallback for edge cases.

**Tech Stack:** Next.js 15, React 19, TypeScript, shadcn/ui, recharts v3.8.1, @libsql/client, Turso, Tailwind v4, lucide-react

**IGA is the home team.** Every metric, every chart, every comparison is framed around "how does IGA beat Thriftway?" Green = IGA winning, red = Thriftway undercutting us.

---

## Phase 1: Product Matcher v5 — AI-Assisted Fuzzy Matching

### Task 1: Analyze unmatched IGA products

**Objective:** Identify which IGA products have no match and why.

**Files:**
- Create: `scrapers/analyze_unmatched.py`

**Step 1: Write analysis script**

```python
"""Analyze unmatched IGA products to understand the gap."""
import json
from scrapers.db import query, execute

# Count unmatched
iga_count = query("SELECT COUNT(*) as c FROM products WHERE store_id='iga-vashon'")[0]["c"]
matched = query("SELECT COUNT(DISTINCT iga_product_id) as c FROM product_matches")[0]["c"]
print(f"IGA products: {iga_count}")
print(f"Matched: {matched} ({matched/iga_count*100:.1f}%)")
print(f"Unmatched: {iga_count - matched}")

# Sample 20 unmatched products
unmatched = query("""
    SELECT p.id, p.name, p.size, p.price, p.upc, p.barcode
    FROM products p
    WHERE p.store_id = 'iga-vashon'
      AND p.id NOT IN (SELECT iga_product_id FROM product_matches)
    LIMIT 20
""")
for p in unmatched:
    print(f"  {p['name']} | size={p['size']} | upc={p['upc']} | barcode={p['barcode']} | ${p['price']}")
```

**Step 2: Run analysis**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
python analyze_unmatched.py
```

**Expected:** ~2,300 unmatched products. Sample of 20 with names and UPCs.

**Step 3: Categorize the unmatched**

Add to the script:
```python
# Categorize unmatched
categories = query("""
    SELECT
        CASE
            WHEN p.upc IS NOT NULL AND p.upc != '' THEN 'has_upc'
            WHEN p.barcode IS NOT NULL AND p.barcode != '' THEN 'has_barcode'
            ELSE 'no_code'
        END as category,
        COUNT(*) as count
    FROM products p
    WHERE p.store_id = 'iga-vashon'
      AND p.id NOT IN (SELECT iga_product_id FROM product_matches)
    GROUP BY category
""")
print("\nUnmatched categories:")
for cat in categories:
    print(f"  {cat['category']}: {cat['count']}")
```

---

### Task 2: Build LLM-assisted matcher script

**Objective:** For products the fuzzy matcher can't match, use an LLM to compare names.

**Files:**
- Create: `scrapers/llm_matcher.py`

**Step 1: Create the LLM matcher**

```python
"""LLM-assisted product matcher for unmatched products.

Uses the matcher's index to find top-3 fuzzy candidates,
then asks the LLM to pick the best match or declare no match.
"""
import json
import re
from scrapers.db import query, execute
from scrapers.matcher import Matcher  # existing fuzzy matcher

IGA_STORE = "iga-vashon"
TW_STORE = "thriftway-vashon"

def normalize_name(name: str) -> str:
    """Normalize product name for LLM comparison."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def llm_match_batch(products: list[dict], candidates_map: dict[str, list[dict]], batch_size=20) -> list[dict]:
    """Use an LLM to match products. Returns list of matches.

    Each product dict has: id, name, size, price, upc, barcode
    Each candidate entry has: id, name, size, price

    We'll delegate this to a subagent that calls an LLM API.
    For now, we structure the data and print the prompt.
    """
    matches = []
    unmatched_remaining = []

    batch = products[:batch_size]

    for product in batch:
        candidates = candidates_map.get(product["id"], [])[:3]
        if not candidates:
            unmatched_remaining.append(product)
            continue

        # Structure the comparison for the LLM
        prompt = format_match_prompt(product, candidates)
        # TODO: Call LLM API with structured output
        # For now, save for batch processing
        matches.append({
            "iga_id": product["id"],
            "iga_name": product["name"],
            "prompt": prompt,
            "candidates": candidates,
        })

    return matches

def format_match_prompt(product: dict, candidates: list[dict]) -> str:
    """Format a product comparison prompt for LLM."""
    lines = [
        "Match this IGA product to the closest Thriftway product, or respond NONE.",
        "",
        f"IGA Product: {product['name']}",
    ]
    if product.get("size"):
        lines.append(f"Size: {product['size']}")
    if product.get("upc"):
        lines.append(f"UPC: {product['upc']}")

    lines.append("\nThriftway Candidates:")
    for i, c in enumerate(candidates):
        lines.append(f"{i+1}. {c['name']}")
        if c.get("size"):
            lines.append(f"   Size: {c['size']}")
        if c.get("price"):
            lines.append(f"   Price: ${c['price']}")

    lines.append("\nRespond with: MATCH: <number> or NONE")
    return "\n".join(lines)

if __name__ == "__main__":
    # Load unmatched IGA products
    unmatched = query(f"""
        SELECT p.id, p.name, p.size, p.price, p.upc, p.barcode
        FROM products p
        WHERE p.store_id = '{IGA_STORE}'
          AND p.id NOT IN (SELECT iga_product_id FROM product_matches)
        ORDER BY p.name
    """)

    print(f"Unmatched IGA products: {len(unmatched)}")

    # For each unmatched, find top fuzzy candidates from Thriftway
    m = Matcher()
    candidates_map = {}
    for product in unmatched[:200]:  # Start with 200
        candidates = m.search(product["name"], store=TW_STORE, limit=5)
        candidates_map[product["id"]] = candidates

    # Format batch for LLM
    batch_results = llm_match_batch(unmatched[:200], candidates_map, batch_size=20)

    # Write prompts to file for batch LLM processing
    with open("llm_match_batch.json", "w") as f:
        json.dump(batch_results, f, indent=2)

    print(f"Wrote {len(batch_results)} items to llm_match_batch.json")
```

**Step 2: Run the prep script**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/scrapers
python llm_matcher.py
```

**Expected:** Creates `llm_match_batch.json` with prompts for LLM comparison.

---

### Task 3: Run AI-assisted matching and persist results

**Objective:** Process LLM results and insert new matches into the database.

**Files:**
- Modify: `scrapers/llm_matcher.py`

**Step 1: Add match insertion logic**

```python
def insert_llm_matches(matches: list[dict]):
    """Insert LLM-confirmed matches into the database."""
    inserted = 0
    for m in matches:
        if m.get("match_result") and m["match_result"] != "NONE":
            # m["match_result"] is like "MATCH: 2" -> candidate index 1
            idx = int(m["match_result"].split(":")[1].strip()) - 1
            if 0 <= idx < len(m["candidates"]):
                tw_id = m["candidates"][idx]["id"]
                execute("""
                    INSERT OR REPLACE INTO product_matches
                        (iga_product_id, thriftway_product_id, match_type, confidence)
                    VALUES (?, ?, 'llm', 0.85)
                """, [m["iga_id"], tw_id])
                inserted += 1

    print(f"Inserted {inserted} LLM-assisted matches")

    # Update stats
    stats = query("""
        SELECT
            (SELECT COUNT(*) FROM products WHERE store_id='iga-vashon') as iga_count,
            (SELECT COUNT(DISTINCT iga_product_id) FROM product_matches) as matched
    """)[0]
    print(f"Coverage: {stats['matched']}/{stats['iga_count']} "
          f"({stats['matched']/stats['iga_count']*100:.1f}%)")
```

**Step 2: Process LLM responses**

The LLM batch processing will be done via a subagent that reads the JSON, calls the LLM API for each batch, and returns structured results. Then `insert_llm_matches` persists them.

---

## Phase 2: Dashboard UI

### Task 4: Update layout with IGA branding

**Objective:** Replace the default Next.js layout with an IGA-themed app shell.

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/globals.css` (if it exists)

**Step 1: Rewrite layout with IGA branding**

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GSW — Grocery Store Wars",
  description: "Competitive intelligence dashboard for IGA Vashon",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-white dark:bg-zinc-950">
        <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                G
              </div>
              <span className="font-semibold text-zinc-900 dark:text-zinc-100">GSW</span>
              <span className="hidden sm:inline text-sm text-zinc-500 dark:text-zinc-400">
                IGA Vashon Intelligence
              </span>
            </div>
            <nav className="flex items-center gap-4 text-sm text-zinc-600 dark:text-zinc-400">
              <a href="#" className="hover:text-zinc-900 dark:hover:text-zinc-100">Dashboard</a>
              <a href="#" className="hover:text-zinc-900 dark:hover:text-zinc-100">Products</a>
              <a href="#" className="hover:text-zinc-900 dark:hover:text-zinc-100">Staples</a>
            </nav>
          </div>
        </header>
        <main className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
```

**Step 2: Verify the layout renders**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm run dev
```

Open http://localhost:3000. Should see IGA-branded header with GSW logo.

---

### Task 5: Build stat cards component

**Objective:** Top-level stat cards showing IGA's competitive position.

**Files:**
- Create: `frontend/src/components/stat-card.tsx`
- Create: `frontend/src/components/stat-grid.tsx`

**Step 1: Create StatCard component**

```tsx
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ title, value, subtitle, trend, trendValue, icon, className }: StatCardProps) {
  return (
    <Card className={cn("p-5", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{title}</p>
          <p className="text-3xl font-bold mt-1 text-zinc-900 dark:text-zinc-100">{value}</p>
          {subtitle && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{subtitle}</p>
          )}
          {trendValue && (
            <div className="flex items-center gap-1 mt-2">
              <span className={cn(
                "text-xs font-medium",
                trend === "up" && "text-emerald-600",
                trend === "down" && "text-red-600",
                trend === "neutral" && "text-zinc-500",
              )}>
                {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
              </span>
            </div>
          )}
        </div>
        {icon && (
          <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
```

**Step 2: Create StatGrid**

```tsx
import { StatCard } from "./stat-card";
import { Store, Package, DollarSign, TrendingUp } from "lucide-react";

interface DashboardStats {
  iga_count: number;
  tw_count: number;
  matched_count: number;
  avg_price_gap: number;
}

interface StatGridProps {
  stats: DashboardStats;
}

export function StatGrid({ stats }: StatGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="IGA Products"
        value={stats.iga_count?.toLocaleString() ?? "—"}
        subtitle="Total catalog"
        icon={<Store className="w-5 h-5 text-emerald-600" />}
      />
      <StatCard
        title="Matched Products"
        value={stats.matched_count?.toLocaleString() ?? "—"}
        subtitle={`${stats.iga_count ? ((stats.matched_count / stats.iga_count) * 100).toFixed(0) : 0}% of IGA catalog`}
        icon={<Package className="w-5 h-5 text-blue-600" />}
      />
      <StatCard
        title="Avg Price Gap"
        value={`$${Math.abs(stats.avg_price_gap || 0).toFixed(2)}`}
        subtitle="IGA vs Thriftway"
        trend={stats.avg_price_gap > 0 ? "up" : "down"}
        trendValue={stats.avg_price_gap > 0 ? "IGA higher" : "IGA lower"}
        icon={<DollarSign className="w-5 h-5 text-amber-600" />}
      />
      <StatCard
        title="Margin Opportunities"
        value={stats.tw_count ? ((stats.matched_count / stats.tw_count) * 100).toFixed(0) + "%" : "—"}
        subtitle="Price adjustment potential"
        icon={<TrendingUp className="w-5 h-5 text-purple-600" />}
      />
    </div>
  );
}
```

**Step 3: Verify components compile**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npx tsc --noEmit
```

---

### Task 6: Build department comparison bar chart

**Objective:** Horizontal bar chart showing avg IGA vs Thriftway prices by department.

**Files:**
- Create: `frontend/src/components/department-chart.tsx`

**Step 1: Create DepartmentChart**

```tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface DepartmentData {
  department_name: string;
  avg_iga_price: number;
  avg_tw_price: number;
  avg_gap: number;
  product_count: number;
}

interface DepartmentChartProps {
  data: DepartmentData[];
}

export function DepartmentChart({ data }: DepartmentChartProps) {
  const chartData = data.map(d => ({
    name: d.department_name || "Unknown",
    IGA: d.avg_iga_price,
    Thriftway: d.avg_tw_price,
    Gap: d.avg_gap,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Department Price Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 40)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 100 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={90} />
            <Tooltip
              formatter={(value: number) => `$${value.toFixed(2)}`}
              contentStyle={{ background: "#fff", border: "1px solid #e4e4e7", borderRadius: "8px" }}
            />
            <Legend />
            <Bar dataKey="IGA" fill="#059669" radius={[0, 4, 4, 0]} />
            <Bar dataKey="Thriftway" fill="#6b7280" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

**Step 2: Verify it compiles**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npx tsc --noEmit
```

---

### Task 7: Build margin opportunities table

**Objective:** Table showing products where IGA is priced below Thriftway and could raise prices.

**Files:**
- Create: `frontend/src/components/margin-table.tsx`

**Step 1: Create MarginTable**

```tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface MarginRow {
  name: string;
  iga_price: number;
  iga_display: string;
  tw_price: number;
  tw_display: string;
  gap: number;
  suggested_price: number;
}

interface MarginTableProps {
  data: MarginRow[];
}

export function MarginTable({ data }: MarginTableProps) {
  if (!data.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Margin Opportunities</CardTitle>
        <p className="text-sm text-zinc-500">Products where IGA is priced below Thriftway — room to raise</p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-800">
                <th className="text-left py-2 font-medium text-zinc-500">Product</th>
                <th className="text-right py-2 font-medium text-zinc-500">IGA</th>
                <th className="text-right py-2 font-medium text-zinc-500">Thriftway</th>
                <th className="text-right py-2 font-medium text-zinc-500">Gap</th>
                <th className="text-right py-2 font-medium text-zinc-500">Suggested</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="border-b border-zinc-100 dark:border-zinc-900">
                  <td className="py-2 pr-4 max-w-[300px] truncate">{row.name}</td>
                  <td className="text-right py-2 text-emerald-600 font-medium">{row.iga_display || `$${row.iga_price?.toFixed(2)}`}</td>
                  <td className="text-right py-2">{row.tw_display || `$${row.tw_price?.toFixed(2)}`}</td>
                  <td className="text-right py-2">
                    <Badge variant="outline" className="text-emerald-600 border-emerald-200">
                      +${row.gap?.toFixed(2)}
                    </Badge>
                  </td>
                  <td className="text-right py-2 font-medium">${row.suggested_price?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

### Task 8: Build staple items comparison table

**Objective:** Side-by-side comparison of staple grocery items.

**Files:**
- Create: `frontend/src/components/staples-table.tsx`

**Step 1: Create StaplesTable**

```tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface StapleRow {
  id: number;
  name: string;
  iga_name: string;
  iga_price: number;
  iga_display: string;
  tw_name: string;
  tw_price: number;
  tw_display: string;
}

interface StaplesTableProps {
  data: StapleRow[];
}

export function StaplesTable({ data }: StaplesTableProps) {
  if (!data.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Staple Item Comparison</CardTitle>
        <p className="text-sm text-zinc-500">Everyday essentials — who wins?</p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-800">
                <th className="text-left py-2 font-medium text-zinc-500">Item</th>
                <th className="text-right py-2 font-medium text-zinc-500">IGA</th>
                <th className="text-right py-2 font-medium text-zinc-500">Thriftway</th>
                <th className="text-right py-2 font-medium text-zinc-500">Winner</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => {
                const igaWins = row.iga_price !== null && row.tw_price !== null && row.iga_price < row.tw_price;
                const twWins = row.iga_price !== null && row.tw_price !== null && row.iga_price > row.tw_price;
                const tie = row.iga_price !== null && row.tw_price !== null && row.iga_price === row.tw_price;

                return (
                  <tr key={i} className="border-b border-zinc-100 dark:border-zinc-900">
                    <td className="py-2 pr-4 font-medium">{row.name}</td>
                    <td className={`text-right py-2 ${igaWins ? 'text-emerald-600 font-medium' : ''}`}>
                      {row.iga_display || (row.iga_price !== null ? `$${row.iga_price.toFixed(2)}` : "—")}
                    </td>
                    <td className={`text-right py-2 ${twWins ? 'text-red-600 font-medium' : ''}`}>
                      {row.tw_display || (row.tw_price !== null ? `$${row.tw_price.toFixed(2)}` : "—")}
                    </td>
                    <td className="text-right py-2">
                      {igaWins && <Badge className="bg-emerald-100 text-emerald-700">IGA</Badge>}
                      {twWins && <Badge className="bg-red-100 text-red-700">Thriftway</Badge>}
                      {tie && <Badge variant="outline">Tie</Badge>}
                      {(row.iga_price === null || row.tw_price === null) && <Badge variant="outline">—</Badge>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

### Task 9: Build price gap distribution chart

**Objective:** Show the distribution of price gaps — are we mostly cheaper or more expensive?

**Files:**
- Create: `frontend/src/components/gap-chart.tsx`

**Step 1: Create GapChart**

```tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface GapChartProps {
  gaps: number[]; // Array of (IGA price - Thriftway price) for each matched product
}

interface BucketData {
  range: string;
  count: number;
  color: string;
}

function bucketGaps(gaps: number[]): BucketData[] {
  const buckets: BucketData[] = [
    { range: "< -$2.00", count: 0, color: "#dc2626" },
    { range: "-$2.00 to -$1.00", count: 0, color: "#ef4444" },
    { range: "-$1.00 to -$0.50", count: 0, color: "#f97316" },
    { range: "-$0.50 to $0.00", count: 0, color: "#eab308" },
    { range: "$0.00 to $0.50", count: 0, color: "#22c55e" },
    { range: "$0.50 to $1.00", count: 0, color: "#16a34a" },
    { range: "$1.00 to $2.00", count: 0, color: "#15803d" },
    { range: "> $2.00", count: 0, color: "#14532d" },
  ];

  for (const gap of gaps) {
    if (gap < -2) buckets[0].count++;
    else if (gap < -1) buckets[1].count++;
    else if (gap < -0.5) buckets[2].count++;
    else if (gap < 0) buckets[3].count++;
    else if (gap < 0.5) buckets[4].count++;
    else if (gap < 1) buckets[5].count++;
    else if (gap < 2) buckets[6].count++;
    else buckets[7].count++;
  }

  return buckets.filter(b => b.count > 0);
}

export function GapChart({ gaps }: GapChartProps) {
  const data = bucketGaps(gaps);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Price Gap Distribution</CardTitle>
        <p className="text-sm text-zinc-500">Negative = IGA cheaper. Positive = IGA more expensive.</p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
            <XAxis dataKey="range" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value: number) => [`${value} products`, "Count"]}
              contentStyle={{ background: "#fff", border: "1px solid #e4e4e7", borderRadius: "8px" }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

---

### Task 10: Wire up the dashboard page

**Objective:** Compose all components into the main dashboard page with live data.

**Files:**
- Rewrite: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/dashboard-client.tsx`

**Step 1: Create client-side dashboard wrapper**

```tsx
"use client";

import { StatGrid } from "./stat-grid";
import { DepartmentChart } from "./department-chart";
import { MarginTable } from "./margin-table";
import { StaplesTable } from "./staples-table";
import { GapChart } from "./gap-chart";

interface DashboardData {
  stats: {
    iga_count: number;
    tw_count: number;
    matched_count: number;
    avg_price_gap: number;
  };
  staples: any[];
  margins: any[];
  departments: any[];
  gaps: number[];
}

interface DashboardClientProps {
  data: DashboardData;
}

export function DashboardClient({ data }: DashboardClientProps) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          IGA Vashon Intelligence Dashboard
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          Competitive pricing analysis vs Thriftway Vashon
        </p>
      </div>

      {/* Stat Cards */}
      <StatGrid stats={data.stats} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DepartmentChart data={data.departments} />
        <GapChart gaps={data.gaps} />
      </div>

      {/* Tables */}
      <MarginTable data={data.margins} />
      <StaplesTable data={data.staples} />
    </div>
  );
}
```

**Step 2: Rewrite page.tsx as server component**

```tsx
import { getDashboardStats, getStapleItems, getMarginOpportunities } from "@/db/queries";
import { getDepartmentComparison } from "@/db/queries";
import { DashboardClient } from "@/components/dashboard-client";
import turso from "@/db";

async function getGapDistribution() {
  const result = await turso.execute(`
    SELECT (ps.price - pt_comp.price) as gap
    FROM product_matches pm
    JOIN products ps ON pm.iga_product_id = ps.id
    JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
    WHERE ps.price IS NOT NULL AND pt_comp.price IS NOT NULL
  `);
  return result.rows.map((r: any) => r.gap as number);
}

export default async function DashboardPage() {
  const [stats, staples, margins, departments, gaps] = await Promise.all([
    getDashboardStats(),
    getStapleItems(),
    getMarginOpportunities(10),
    getDepartmentComparison(),
    getGapDistribution(),
  ]);

  return (
    <DashboardClient
      data={{
        stats: {
          iga_count: stats.iga_count as number,
          tw_count: stats.tw_count as number,
          matched_count: stats.matched_count as number,
          avg_price_gap: stats.avg_price_gap as number,
        },
        staples: staples as any[],
        margins: margins as any[],
        departments: departments as any[],
        gaps,
      }}
    />
  );
}
```

**Step 3: Run the dev server and test**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm run dev
```

Visit http://localhost:3000. All four stat cards should render with live data. Department chart and gap chart should render. Tables should show margin opportunities and staples.

---

### Task 11: Add loading states and error handling

**Objective:** Graceful loading and error states for each component.

**Files:**
- Modify: `frontend/src/components/dashboard-client.tsx`

**Step 1: Add Suspense boundaries and error states**

In `page.tsx`, wrap the data-dependent components in Suspense. Add a `loading.tsx` file for the page route:

```tsx
// frontend/src/app/loading.tsx
import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
    </div>
  );
}
```

**Step 2: Add error boundary**

```tsx
// frontend/src/app/error.tsx
"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-32 text-center">
      <h2 className="text-xl font-semibold text-red-600 mb-2">Something went wrong</h2>
      <p className="text-zinc-500 mb-4">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm hover:bg-zinc-800"
      >
        Try again
      </button>
    </div>
  );
}
```

---

## Phase 3: Polish & Deploy

### Task 12: Responsive polish and dark mode

**Objective:** Ensure dashboard looks great on mobile and in dark mode.

**Files:**
- Modify: Various component files

**Step 1: Test responsive layout**

- Stack stat cards to 1 column on mobile (< 640px)
- Department chart switches to vertical bars on mobile
- Tables scroll horizontally on small screens
- Margin table column widths adjust

**Step 2: Verify dark mode**

All components use `dark:` Tailwind variants. Test by toggling dark mode in browser DevTools.

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm run dev
```

---

### Task 13: Deploy to here.now with custom domain

**Objective:** Build and deploy the dashboard to a custom subdomain.

**Files:**
- Create: `frontend/.env.local` (for deployment config)

**Step 1: Build the Next.js app**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npm run build
```

**Step 2: Deploy to here.now**

```bash
cd /Users/johngoad/workspace/grocery-store-wars/frontend
npx here-now publish --path out --slug gsw-dashboard
```

**Step 3: Link to custom subdomain**

```bash
curl -X POST https://here.now/api/domains/link \
  -H "Authorization: Bearer $HERE_NOW_TOKEN" \
  -d '{"domain": "gsw.goad.net", "slug": "gsw-dashboard"}'
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-3 | Product matcher v5 with AI fallback |
| 2 | 4-10 | Dashboard UI — layout, stats, charts, tables |
| 3 | 11-13 | Polish, error handling, deploy |
