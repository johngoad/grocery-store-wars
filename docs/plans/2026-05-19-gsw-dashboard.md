# GSW Dashboard — IGA Competitive Intelligence

> **For Hermes:** Use subagent-driven-development skill to implement task-by-task.

**Goal:** Build a beautiful, data-rich dashboard for IGA Vashon that shows competitive intelligence against Thriftway — staple item comparisons, price gap charts, margin opportunities, and department-level analytics.

**Architecture:** Next.js 16 App Router with server-side API routes backed by Turso (SQLite). All data flows through existing `/api/*` endpoints. Dashboard is a single page with collapsible sections. Recharts for charts, shadcn/ui for components, Tailwind v4 for styling.

**Tech Stack:** Next.js 16, React 19, TypeScript, Recharts 3, shadcn/ui, Tailwind v4, Lucide icons, @libsql/client

**Design:** Dark theme by default (IGA competitive intel), green accent (#22c55e / emerald-500), clean card-based layout. Professional grocery analytics dashboard feel — not a consumer app.

---

## Data Flow

```
Turso DB → db/queries.ts → API routes → fetch in page.tsx → React components
```

All API routes return JSON. No server components needed — client-side fetch with loading states.

### API Endpoints

| Endpoint | Returns | Used By |
|----------|---------|---------|
| `/api/dashboard` | `{ stats, staples, margins }` | Main page |
| `/api/departments` | Department comparison array | Department chart |
| `/api/margins?limit=20` | Top margin opportunities | Margin table |
| `/api/staples` | Staple items with both stores | Staple comparison |

---

### Task 1: TypeScript Types

**Objective:** Define TypeScript interfaces for all API responses

**Files:**
- Create: `frontend/src/types/index.ts`

**Types needed:**
```typescript
export interface DashboardStats {
  iga_count: number;
  tw_count: number;
  matched_count: number;
  avg_price_gap: number;
}

export interface StapleItem {
  id: number;
  name: string;
  category: string;
  display_order: number;
  iga_name: string;
  iga_price: number | null;
  iga_display: string | null;
  tw_name: string;
  tw_price: number | null;
  tw_display: string | null;
}

export interface MarginOpportunity {
  name: string;
  iga_price: number;
  iga_display: string;
  tw_price: number;
  tw_display: string;
  gap: number;
  suggested_price: number;
}

export interface DepartmentComparison {
  department_id: string;
  department_name: string;
  product_count: number;
  avg_iga_price: number;
  avg_tw_price: number;
  avg_gap: number;
}

export interface DashboardData {
  stats: DashboardStats;
  staples: StapleItem[];
  margins: MarginOpportunity[];
}
```

---

### Task 2: Layout Update

**Objective:** Update layout.tsx with IGA branding, metadata, and navigation

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/globals.css` (add dark theme defaults)

**Changes:**
1. Update metadata: title = "GSW — IGA Competitive Intelligence", description about Vashon grocery analytics
2. Add a minimal top nav with "IGA vs Thriftway" branding
3. Set dark theme as default in globals.css
4. Keep Geist font

---

### Task 3: Stat Card Component

**Objective:** Reusable stat card with icon, label, value, and optional trend indicator

**Files:**
- Create: `frontend/src/components/stat-card.tsx`

**Props:**
```typescript
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sublabel?: string;
  trend?: "up" | "down" | "neutral";
}
```

---

### Task 4: Staple Items Table

**Objective:** Side-by-side price comparison table for staple items (eggs, milk, butter, mayonnaise, bread, etc.)

**Files:**
- Create: `frontend/src/components/staple-table.tsx`

**Features:**
- Rows: one per staple item
- Columns: Item name, IGA price, Thriftway price, Difference (with green/red coloring for IGA advantage/disadvantage)
- Sortable by difference
- Winner indicator (green checkmark or dollar sign on cheaper store)
- Loading skeleton state

---

### Task 5: Department Chart

**Objective:** Recharts bar chart showing department-level price comparison

**Files:**
- Create: `frontend/src/components/department-chart.tsx`

**Features:**
- Horizontal bar chart (departments on Y axis)
- Two bars per department: IGA avg price vs Thriftway avg price
- Green for IGA, amber for Thriftway
- Responsive, dark-themed
- Loading state

---

### Task 6: Margin Opportunities Table

**Objective:** Table showing products where IGA could raise prices

**Files:**
- Create: `frontend/src/components/margin-table.tsx`

**Features:**
- Sorted by gap (largest first)
- Columns: Product name, IGA price, Thriftway price, Gap, Suggested new price
- Green highlighting for products where IGA is significantly cheaper
- Loading skeleton state

---

### Task 7: Main Dashboard Page

**Objective:** Assemble all components into the main dashboard page

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Layout:**
```
┌─────────────────────────────────────┐
│  NAV: IGA Competitive Intelligence  │
├─────────────────────────────────────┤
│  [Stat Card] [Stat Card] [Stat Card]│
│  Products    Matched    Avg Gap     │
├─────────────────────────────────────┤
│  STAPLE ITEMS — Side by Side       │
│  [Staple Table with comparisons]    │
├─────────────────────────────────────┤
│  DEPARTMENT BREAKDOWN              │
│  [Recharts Bar Chart]              │
├─────────────────────────────────────┤
│  MARGIN OPPORTUNITIES              │
│  [Products where IGA can raise $]  │
└─────────────────────────────────────┘
```

**Features:**
- Fetches `/api/dashboard` for stats + staples + top 10 margins
- Fetches `/api/departments` for department chart
- Fetches `/api/margins?limit=20` for full margin table
- Loading skeletons while fetching
- Error states with retry buttons
- Empty states ("No staples configured" etc.)
- Responsive — stacks on mobile

---

### Task 8: Polish and Verify

**Objective:** Final integration test, visual polish, responsive check

**Files:**
- None new, review all above

**Checks:**
- All data fetching works (verify against live API)
- Loading states appear and resolve
- Error states handle API failure gracefully
- Dark theme is consistent
- Mobile layout doesn't break
- Staple items show real data (eggs, milk, butter, mayo)
- Department chart renders with actual departments
- Margin table shows actionable opportunities
