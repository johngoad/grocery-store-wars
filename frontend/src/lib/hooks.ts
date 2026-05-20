import { useEffect, useState, useCallback } from "react";
import type { DepartmentComparison } from "@/types";

interface UseDepartmentsResult {
  departments: DepartmentComparison[] | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDepartments(): UseDepartmentsResult {
  const [departments, setDepartments] = useState<DepartmentComparison[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDepartments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/departments");
      if (!res.ok) {
        throw new Error(`Department fetch failed with status ${res.status}`);
      }
      const data: DepartmentComparison[] = await res.json();
      setDepartments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load departments");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  return { departments, isLoading, error, refetch: fetchDepartments };
}
