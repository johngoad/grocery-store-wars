"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Package, GitCompare, DollarSign, TrendingDown } from "lucide-react";
import { useData } from "@/hooks/useData";

export function StatsCards() {
  const { data, isLoading, error } = useData("/api/dashboard");

  if (error) {
    return (
      <div className="text-red-500 text-sm bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        Failed to load stats: {error}
      </div>
    );
  }

  const stats = data?.stats;

  const cards = [
    {
      label: "IGA Products",
      value: stats?.iga_count,
      icon: Package,
      color: "text-emerald-600 dark:text-emerald-400",
      bg: "bg-emerald-50 dark:bg-emerald-950",
    },
    {
      label: "Matched vs TW",
      value: stats?.matched_count,
      icon: GitCompare,
      color: "text-blue-600 dark:text-blue-400",
      bg: "bg-blue-50 dark:bg-blue-950",
    },
    {
      label: "Avg Price Gap",
      value:
        stats?.avg_price_gap != null
          ? `${Number(stats.avg_price_gap) < 0 ? "" : "+"}$${Number(
              stats.avg_price_gap
            ).toFixed(2)}`
          : null,
      icon: DollarSign,
      color:
        Number(stats?.avg_price_gap) < 0
          ? "text-emerald-600 dark:text-emerald-400"
          : "text-red-600 dark:text-red-400",
      bg:
        Number(stats?.avg_price_gap) < 0
          ? "bg-emerald-50 dark:bg-emerald-950"
          : "bg-red-50 dark:bg-red-950",
    },
    {
      label: "Thriftway Products",
      value: stats?.tw_count,
      icon: TrendingDown,
      color: "text-zinc-600 dark:text-zinc-400",
      bg: "bg-zinc-50 dark:bg-zinc-900",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.label} className={card.bg}>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">
                {card.label}
              </p>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </div>
            {isLoading ? (
              <Skeleton className="h-9 w-24 mt-1" />
            ) : (
              <p className={`text-3xl font-bold mt-1 ${card.color}`}>
                {card.value?.toLocaleString?.() ?? card.value ?? "—"}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
