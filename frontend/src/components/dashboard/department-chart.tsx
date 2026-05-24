"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { useData } from "@/hooks/useData";
import { ExternalLink } from "lucide-react";

const DEPT_FILTER = ["Produce", "Meat", "Dairy", "Eggs", "Milk", "Cheese"];
const DEPT_SLUGS: Record<string, string> = {
  Produce: "produce", Meat: "meat", Dairy: "dairy",
  Eggs: "dairy", Milk: "dairy", Cheese: "dairy",
};

export function DepartmentChart() {
  const { data, isLoading } = useData("/api/departments");

  const chartData = (data || [])
    .filter((d: any) => DEPT_FILTER.includes(d.department_name))
    .sort((a: any, b: any) => Number(b.avg_gap) - Number(a.avg_gap))
    .map((d: any) => {
      const igaPrice = Number(d.avg_iga_price);
      const twPrice = Number(d.avg_tw_price);
      const gap = igaPrice - twPrice;
      return {
        name: d.department_name || "Unknown",
        IGA: igaPrice,
        Thriftway: twPrice,
        gap: Number(d.avg_gap),
        gapDisplay: gap > 0 ? `+$${gap.toFixed(2)}` : `-$${Math.abs(gap).toFixed(2)}`,
        igaHigher: gap > 0,
        count: d.product_count,
        slug: DEPT_SLUGS[d.department_name] || d.department_name?.toLowerCase(),
      };
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Department Price Comparison</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-80 w-full" /></CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Department Price Comparison</CardTitle>
        <p className="text-sm text-muted-foreground">Average price by department with gap to competitor</p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 44)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 70, right: 80, top: 5, bottom: 5 }}
            barGap={2}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "var(--foreground)", fontWeight: 500 }} width={70} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--popover)", border: "1px solid var(--border)", borderRadius: "12px",
                fontSize: "13px", color: "var(--popover-foreground)",
              }}
              formatter={(value: any) => [`$${Number(value).toFixed(2)}`, ""]}
            />
            <Bar dataKey="IGA" fill="#10b981" radius={[0, 4, 4, 0]} barSize={14} />
            <Bar dataKey="Thriftway" fill="#6b7280" radius={[0, 4, 4, 0]} barSize={14} />
          </BarChart>
        </ResponsiveContainer>
        <div className="flex items-center gap-3 mt-4 pt-3 border-t border-border">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="w-3 h-3 rounded-sm bg-emerald-500" /> IGA
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="w-3 h-3 rounded-sm bg-zinc-500" /> Thriftway
          </div>
          <div className="flex-1" />
          <div className="flex flex-wrap gap-2">
            {["produce", "meat", "dairy"].map(slug => (
              <Link key={slug} href={`/departments/${slug}`}
                className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-muted hover:bg-accent text-muted-foreground hover:text-foreground transition-all border border-border">
                {slug.charAt(0).toUpperCase() + slug.slice(1)} <ExternalLink className="h-3 w-3" />
              </Link>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
