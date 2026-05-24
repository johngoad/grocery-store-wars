"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Package, GitCompare, DollarSign, Store, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { useData } from "@/hooks/useData";

export function StatsCards() {
  const { data, isLoading, error } = useData("/api/dashboard");

  if (error) {
    return (
      <div className="text-destructive text-sm bg-destructive/10 border border-destructive/20 rounded-xl p-4 backdrop-blur">
        Failed to load stats: {error}
      </div>
    );
  }

  const stats = data?.stats;
  const gap = Number(stats?.avg_price_gap ?? 0);
  const direction = gap < -0.05 ? "down" : gap > 0.05 ? "up" : "flat";

  const cards = [
    {
      label: "IGA Products",
      value: stats?.iga_count?.toLocaleString(),
      subtitle: "Tracked & monitored",
      icon: Package,
      color: "emerald",
    },
    {
      label: "Matched vs TW",
      value: stats?.matched_count?.toLocaleString(),
      subtitle: `${stats?.iga_count ? Math.round(stats.matched_count / stats.iga_count * 100) : 0}% coverage`,
      icon: GitCompare,
      color: "blue",
    },
    {
      label: "Avg Price Gap",
      value: gap !== 0 ? `${gap > 0 ? "+" : ""}$${Math.abs(gap).toFixed(2)}` : "$0.00",
      subtitle: direction === "up" ? "IGA above market" : direction === "down" ? "IGA below market" : "Price matched",
      icon: direction === "up" ? ArrowUpRight : direction === "down" ? ArrowDownRight : Minus,
      color: direction === "up" ? "red" : direction === "down" ? "emerald" : "amber",
    },
    {
      label: "Thriftway Products",
      value: stats?.tw_count?.toLocaleString(),
      subtitle: "Competitor catalog",
      icon: Store,
      color: "zinc",
    },
  ];

  const colorClasses: Record<string, { border: string; iconBg: string; iconColor: string; valueColor: string }> = {
    emerald: { border: "border-emerald-200 dark:border-emerald-500/20", iconBg: "bg-emerald-50 dark:bg-emerald-500/10", iconColor: "text-emerald-600 dark:text-emerald-400", valueColor: "text-emerald-700 dark:text-emerald-300" },
    blue: { border: "border-blue-200 dark:border-blue-500/20", iconBg: "bg-blue-50 dark:bg-blue-500/10", iconColor: "text-blue-600 dark:text-blue-400", valueColor: "text-blue-700 dark:text-blue-300" },
    red: { border: "border-red-200 dark:border-red-500/20", iconBg: "bg-red-50 dark:bg-red-500/10", iconColor: "text-red-600 dark:text-red-400", valueColor: "text-red-700 dark:text-red-300" },
    amber: { border: "border-amber-200 dark:border-amber-500/20", iconBg: "bg-amber-50 dark:bg-amber-500/10", iconColor: "text-amber-600 dark:text-amber-400", valueColor: "text-amber-700 dark:text-amber-300" },
    zinc: { border: "border-border", iconBg: "bg-muted", iconColor: "text-muted-foreground", valueColor: "text-foreground" },
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const cls = colorClasses[card.color];
        return (
          <Card key={card.label} className={`${cls.border} bg-card border backdrop-blur-sm`}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {card.label}
                </p>
                <div className={`h-8 w-8 rounded-lg ${cls.iconBg} flex items-center justify-center`}>
                  <card.icon className={`h-4 w-4 ${cls.iconColor}`} />
                </div>
              </div>
              {isLoading ? (
                <Skeleton className="h-10 w-28 mt-1" />
              ) : (
                <>
                  <p className={`text-3xl font-bold tracking-tight font-mono-data ${cls.valueColor}`}>
                    {card.value ?? "—"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1 font-medium">{card.subtitle}</p>
                </>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
