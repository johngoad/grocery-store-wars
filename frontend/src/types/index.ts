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
  iga_name: string | null;
  iga_price: number | null;
  iga_display: string | null;
  tw_name: string | null;
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
