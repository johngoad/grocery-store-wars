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
    .sort((a: any, b: any) => b.product_count - a.product_count)
    .map((d: any) => ({
    name: d.department_name || "Unknown",
    IGA: Number(d.avg_iga_price),
    Thriftway: Number(d.avg_tw_price),
    gap: Number(d.avg_gap),
    count: d.product_count,
  }));

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Department Price Comparison</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-80 w-full" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Department Price Comparison</CardTitle>
        <p className="text-sm text-zinc-500">Average price per department — IGA vs Thriftway</p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 36)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 70, right: 30, top: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-800" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={65} />
            <Tooltip contentStyle={{ backgroundColor: "var(--background)", border: "1px solid var(--border)", borderRadius: "8px", fontSize: "13px" }} formatter={(value: any, name: any) => [`$${Number(value).toFixed(2)}`, name]} />
            <Bar dataKey="IGA" fill="#10b981" radius={[0, 4, 4, 0]} barSize={12} />
            <Bar dataKey="Thriftway" fill="#6b7280" radius={[0, 4, 4, 0]} barSize={12} />
          </BarChart>
        </ResponsiveContainer>
        <div className="flex flex-wrap gap-2 mt-4">
          {["produce", "meat", "dairy"].map(slug => (
            <Link key={slug} href={`/departments/${slug}`}
              className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-400 transition-colors">
              {slug.charAt(0).toUpperCase() + slug.slice(1)} <ExternalLink className="h-3 w-3" />
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
