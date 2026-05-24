"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ZoomIn, CheckCircle2 } from "lucide-react";
import { useData } from "@/hooks/useData";

function formatSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 14 ? s.substring(0, 14) : s;
}

const cheaperBadge = "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20";
const pricierBadge = "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20";
const cheaperText = "text-emerald-600 dark:text-emerald-400";
const pricierText = "text-red-600 dark:text-red-400";

export function NeedsReviewTable() {
  const { data, isLoading } = useData("/api/needs-review");

  if (isLoading) {
    return (
      <Card><CardHeader><CardTitle>Needs Review</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-80 w-full" /></CardContent></Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card className="border-blue-200 dark:border-blue-500/10">
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center">
              <CheckCircle2 className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Needs Review</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">All clear — no suspicious matches found</p>
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="border-blue-200 dark:border-blue-500/10">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center">
              <ZoomIn className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Needs Review</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">Same product size, price gap &gt; $3 — verify manually</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/20 font-mono-data text-xs">
            {data.length} items
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs text-muted-foreground font-medium">IGA Product</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium">IGA</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium">Thriftway</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium w-16">Size</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium">Gap</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row: any, i: number) => {
              const igaCheaper = Number(row.iga_price) < Number(row.tw_price);
              return (
                <TableRow key={i} className="border-border hover:bg-muted/50 transition-colors">
                  <TableCell className="font-medium text-sm max-w-[200px] truncate">{row.name}</TableCell>
                  <TableCell className={`text-right font-mono-data text-sm ${igaCheaper ? cheaperText : pricierText}`}>
                    {row.iga_display}
                  </TableCell>
                  <TableCell className="text-right font-mono-data text-sm text-muted-foreground">{row.tw_display}</TableCell>
                  <TableCell className="text-right text-xs text-muted-foreground">{formatSize(row.iga_size)}</TableCell>
                  <TableCell className="text-right">
                    <Badge className={`font-mono-data text-xs ${igaCheaper ? cheaperBadge : pricierBadge}`}>
                      {igaCheaper ? "+" : "-"}${Number(row.gap).toFixed(2)}
                    </Badge>
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
