"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ZoomIn } from "lucide-react";
import { useData } from "@/hooks/useData";

function formatSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 14 ? s.substring(0, 14) : s;
}

export function NeedsReviewTable() {
  const { data, isLoading } = useData("/api/needs-review");

  if (isLoading) {
    return <Card><CardHeader><CardTitle>Needs Review</CardTitle></CardHeader><CardContent><Skeleton className="h-80 w-full" /></CardContent></Card>;
  }

  if (!data || data.length === 0) {
    return (
      <Card className="border-amber-200 dark:border-amber-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><ZoomIn className="h-5 w-5 text-amber-500" />Needs Review</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-zinc-500">No suspicious matches found — all clear!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-amber-200 dark:border-amber-900">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><ZoomIn className="h-5 w-5 text-amber-500" />Needs Review</CardTitle>
          <Badge variant="outline" className="text-amber-600 border-amber-300 dark:border-amber-700">{data.length} items</Badge>
        </div>
        <p className="text-sm text-zinc-500">Same product size, but price gap &gt; $3. Verify these manually.</p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader><TableRow>
            <TableHead>IGA Product</TableHead>
            <TableHead className="text-right">IGA</TableHead>
            <TableHead className="text-right">Thriftway</TableHead>
            <TableHead className="text-right w-16">Size</TableHead>
            <TableHead className="text-right">Gap</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {data.map((row: any, i: number) => {
              const igaCheaper = Number(row.iga_price) < Number(row.tw_price);
              return (
                <TableRow key={i} className={igaCheaper ? "bg-emerald-50/30 dark:bg-emerald-950/20" : "bg-red-50/30 dark:bg-red-950/20"}>
                  <TableCell className="font-medium max-w-[180px] truncate">{row.name}</TableCell>
                  <TableCell className="text-right text-xs">{row.iga_display}</TableCell>
                  <TableCell className="text-right text-xs">{row.tw_display}</TableCell>
                  <TableCell className="text-right text-xs text-zinc-500">{formatSize(row.iga_size)}</TableCell>
                  <TableCell className="text-right">
                    <span className={`font-semibold text-sm ${igaCheaper ? "text-emerald-600" : "text-red-600"}`}>
                      {igaCheaper ? "+" : "-"}${Number(row.gap).toFixed(2)}
                    </span>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
