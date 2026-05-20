"use client";

import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export interface DashboardStats {
  iga_count: number;
  tw_count: number;
  matched_count: number;
  avg_price_gap: number;
}

export interface DepartmentData {
  department_id: string;
  department_name: string;
  product_count: number;
  avg_iga_price: number;
  avg_tw_price: number;
  avg_gap: number;
}

export interface MarginData {
  name: string;
  iga_price: number;
  iga_display: string;
  tw_price: number;
  tw_display: string;
  gap: number;
  suggested_price: number;
}

export interface StapleData {
  id: number;
  iga_product_id: string;
  thriftway_product_id: string;
  display_order: number;
  iga_name: string;
  iga_price: number | null;
  iga_display: string;
  tw_name: string;
  tw_price: number | null;
  tw_display: string;
}

export function useDashboard() {
  const { data, error, isLoading } = useSWR<{
    stats: DashboardStats;
    staples: StapleData[];
    margins: MarginData[];
  }>("/api/dashboard", fetcher, {
    refreshInterval: 60_000,
  });

  return {
    stats: data?.stats ?? null,
    staples: data?.staples ?? [],
    margins: data?.margins ?? [],
    isLoading,
    isError: !!error,
  };
}

export function useDepartments() {
  const { data, error, isLoading } = useSWR<DepartmentData[]>(
    "/api/departments",
    fetcher,
    { refreshInterval: 60_000 }
  );

  return {
    departments: data ?? [],
    isLoading,
    isError: !!error,
  };
}

export function useMargins(limit = 20) {
  const { data, error, isLoading } = useSWR<MarginData[]>(
    `/api/margins?limit=${limit}`,
    fetcher,
    { refreshInterval: 60_000 }
  );

  return {
    margins: data ?? [],
    isLoading,
    isError: !!error,
  };
}

export function useStaples() {
  const { data, error, isLoading } = useSWR<StapleData[]>(
    "/api/staples",
    fetcher,
    { refreshInterval: 60_000 }
  );

  return {
    staples: data ?? [],
    isLoading,
    isError: !!error,
  };
}

export function usePriceDistribution() {
  const { data, error, isLoading } = useSWR<MarginData[]>(
    "/api/margins?limit=500",
    fetcher,
    { refreshInterval: 60_000 }
  );

  const margins = data ?? [];

  if (margins.length === 0) {
    return { distribution: [], isLoading, isError: !!error };
  }

  const gaps = margins.map((m) => m.gap);
  const min = Math.min(...gaps);
  const max = Math.max(...gaps);
  const range = max - min || 1;
  const binCount = 14;
  const binWidth = range / binCount;

  const bins = Array.from({ length: binCount }, (_, i) => {
    const binStart = min + i * binWidth;
    const binEnd = binStart + binWidth;
    const count = gaps.filter(
      (g) => g >= binStart && (i === binCount - 1 ? g <= binEnd : g < binEnd)
    ).length;
    return {
      label: `$${binStart.toFixed(1)} – $${binEnd.toFixed(1)}`,
      count,
    };
  }).filter((b) => b.count > 0);

  return {
    distribution: bins,
    isLoading,
    isError: !!error,
  };
}
