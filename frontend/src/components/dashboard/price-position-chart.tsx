"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useData } from "@/hooks/useData";

function binGaps(gaps: number[]) {
  const bucketSize = 0.5;
  const bins: Record<string, { range: string; count: number; color: string; low: number }> = {};
  for (const gap of gaps) {
    const bucketLow = Math.floor(gap / bucketSize) * bucketSize;
    const key = `${bucketLow.toFixed(2)}`;
    if (!bins[key]) {
      const color = bucketLow < -0.25 ? "#10b981" : bucketLow > 0.25 ? "#ef4444" : "#f59e0b";
      bins[key] = {
        range: bucketLow < 0
          ? `-$${Math.abs(bucketLow).toFixed(2)} to -$${Math.abs(bucketLow + bucketSize).toFixed(2)}`
          : `$${bucketLow.toFixed(2)} to $${(bucketLow + bucketSize).toFixed(2)}`,
        count: 0, color, low: bucketLow,
      };
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
    return <Card><CardHeader><CardTitle>Price Position Distribution</CardTitle></CardHeader><CardContent><Skeleton className="h-72 w-full" /></CardContent></Card>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price Position vs Thriftway</CardTitle>
        <p className="text-sm text-zinc-500">How IGA prices compare across all matched products</p>
      </CardHeader>
      <CardContent>
        {summary && (
          <div className="flex items-center gap-2 mb-4 text-xs">
            <div className="flex-1 h-2 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden flex">
              <div className="h-full bg-emerald-500" style={{ width: `${(summary.cheaper / summary.total) * 100}%` }} />
              <div className="h-full bg-amber-500" style={{ width: `${(summary.parity / summary.total) * 100}%` }} />
              <div className="h-full bg-red-500" style={{ width: `${(summary.pricier / summary.total) * 100}%` }} />
            </div>
            <span className="text-emerald-600 font-medium">{summary.cheaper} cheaper</span>
            <span className="text-amber-600 font-medium">{summary.parity} parity</span>
            <span className="text-red-600 font-medium">{summary.pricier} pricier</span>
          </div>
        )}
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-800" />
            <XAxis dataKey="range" tick={{ fontSize: 9 }} angle={-35} textAnchor="end" height={65} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(value: any) => [`${value} products`, "Count"]} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (<Cell key={index} fill={entry.color} />))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex items-center gap-4 mt-3 text-xs text-zinc-500 justify-center">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-emerald-500" /> IGA cheaper</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-amber-500" /> Near parity</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-red-500" /> IGA pricier</span>
        </div>
      </CardContent>
    </Card>
  );
}
