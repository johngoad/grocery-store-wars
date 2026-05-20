"use client";

import { useState, useEffect, useCallback } from "react";

interface UseDataResult<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  refresh: () => void;
}

/**
 * Custom hook for client-side data fetching with auto-refresh.
 * Replaces SWR — same skeleton loading pattern, zero dependencies.
 * Refreshes every 5 minutes by default. Pass 0 to disable.
 */
export function useData<T = any>(
  url: string | null,
  refreshInterval = 300_000
): UseDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!url) return;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch");
    } finally {
      setIsLoading(false);
    }
  }, [url]);

  useEffect(() => {
    setIsLoading(true);
    fetchData();

    if (refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, refreshInterval]);

  return { data, error, isLoading, refresh: fetchData };
}
