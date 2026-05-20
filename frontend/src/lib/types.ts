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
  iga_product_id: string;
  thriftway_product_id: string;
  display_order: number;
  iga_name: string;
  iga_price: number;
  iga_display: string;
  tw_name: string;
  tw_price: number;
  tw_display: string;
}

export interface Department {
  department_id: string;
  department_name: string;
  product_count: number;
  avg_iga_price: number;
  avg_tw_price: number;
  avg_gap: number;
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

export interface PriceDistribution {
  range: string;
  label: string;
  count: number;
  color: 'green' | 'amber' | 'red';
}
