"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import { useData } from "@/hooks/useData";
import { ArrowDown, ArrowUp, Equal } from "lucide-react";

function binGaps(gaps: number[]) {
  const bucketSize = 0.50;
  const bins: Record<string, { range: string; count: number; color: string; low: number; label: string }> = {};
  for (const gap of gaps) {
    const bucketLow = Math.floor(gap / bucketSize) * bucketSize;
    const key = `${bucketLow.toFixed(2)}`;
    if (!bins[key]) {
      const color = bucketLow < -0.25 ? "#10b981" : bucketLow > 0.25 ? "#ef4444" : "#f59e0b";
      const label = bucketLow < 0
        ? `IGA -$${Math.abs(bucketLow).toFixed(2)}`
        : `IGA +$${bucketLow.toFixed(2)}`;
      bins[key] = { range: label, count: 0, color, low: bucketLow, label };
    }
    bins[key].count++;
  }
  return Object.values(bins).sort((a, b) => a.low - b.low);
}

export function PricePositionChart() {
  const { data, isLoading } = useData("/api/prices/distribution");
  const chartData = data?.gaps ? binGaps(data.gaps) : [];
  const summary = data?.summary;

  if (isLoading) {
    return (
      <Card><CardHeader><CardTitle>Price Position</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-72 w-full" /></CardContent></Card>
    );
  }

  const gaugeBox = "rounded-xl p-3 text-center border";

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Price Position vs Thriftway</CardTitle>
        <p className="text-sm text-muted-foreground">Distribution of IGA price gaps against competitor</p>
      </CardHeader>
      <CardContent>
        {summary && (
          <div className="grid grid-cols-3 gap-3 mb-5">
            <div className={`${gaugeBox} bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20`}>
              <div className="flex items-center justify-center gap-1 text-emerald-600 dark:text-emerald-400 mb-1">
                <ArrowDown className="h-3.5 w-3.5" />
                <span className="text-lg font-bold font-mono-data">{summary.cheaper}</span>
              </div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Cheaper</p>
            </div>
            <div className={`${gaugeBox} bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20`}>
              <div className="flex items-center justify-center gap-1 text-amber-600 dark:text-amber-400 mb-1">
                <Equal className="h-3.5 w-3.5" />
                <span className="text-lg font-bold font-mono-data">{summary.parity}</span>
              </div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Parity</p>
            </div>
            <div className={`${gaugeBox} bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20`}>
              <div className="flex items-center justify-center gap-1 text-red-600 dark:text-red-400 mb-1">
                <ArrowUp className="h-3.5 w-3.5" />
                <span className="text-lg font-bold font-mono-data">{summary.pricier}</span>
              </div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Pricier</p>
            </div>
          </div>
        )}
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 9, fill: "var(--muted-foreground)" }} angle={-30} textAnchor="end" height={55} interval={0} />
            <YAxis tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} width={30} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--popover)", border: "1px solid var(--border)", borderRadius: "12px",
                fontSize: "12px", color: "var(--popover-foreground)",
              }}
              formatter={(value: any) => [`${value} products`, "Count"]}
              labelFormatter={(label: any) => `Price gap: ${label}`}
            />
            <ReferenceLine y={0} stroke="var(--border)" />
            <Bar dataKey="count" radius={[3, 3, 0, 0]} maxBarSize={40}>
              {chartData.map((entry, index) => (<Cell key={index} fill={entry.color} />))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex items-center justify-center gap-4 mt-3 pt-3 border-t border-border">
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> Cheaper</span>
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground"><span className="w-2.5 h-2.5 rounded-sm bg-amber-500" /> Parity</span>
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground"><span className="w-2.5 h-2.5 rounded-sm bg-red-500" /> Pricier</span>
        </div>
      </CardContent>
    </Card>
  );
}
