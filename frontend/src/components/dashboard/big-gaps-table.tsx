"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ArrowDown, ArrowUp } from "lucide-react";
import { useData } from "@/hooks/useData";

function formatSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 12 ? s.substring(0, 12) : s;
}

export function BigGapsTable() {
  const undercut = useData("/api/margins?limit=10&direction=undercut");
  const raise = useData("/api/margins?limit=10&direction=raise");
  const isLoading = undercut.isLoading || raise.isLoading;

  if (isLoading) {
    return <Card><CardHeader><CardTitle>Big Price Gaps</CardTitle></CardHeader><CardContent><Skeleton className="h-96 w-full" /></CardContent></Card>;
  }

  return (
    <Card className="border-red-200 dark:border-red-900">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" />Big Price Gaps</CardTitle>
        </div>
        <p className="text-sm text-zinc-500">Largest price differences. Sizes shown where available.</p>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Undercut — IGA more expensive */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <ArrowDown className="h-4 w-4 text-red-500" /><h3 className="font-semibold text-red-600 dark:text-red-400">Lower These Prices to Compete</h3>
            <Badge variant="outline" className="text-red-600 border-red-300 dark:border-red-700 text-xs">IGA pricier</Badge>
          </div>
          <Table>
            <TableHeader><TableRow>
              <TableHead>Product</TableHead>
              <TableHead className="text-right">IGA</TableHead>
              <TableHead className="text-right">TW</TableHead>
              <TableHead className="text-right w-14">Size</TableHead>
              <TableHead className="text-right">Gap</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {(undercut.data || []).map((row: any, i: number) => (
                <TableRow key={i} className="bg-red-50/30 dark:bg-red-950/20">
                  <TableCell className="font-medium max-w-[180px] truncate">{row.name}</TableCell>
                  <TableCell className="text-right text-red-600 font-medium text-xs">{row.iga_display}</TableCell>
                  <TableCell className="text-right text-zinc-500 text-xs">{row.tw_display}</TableCell>
                  <TableCell className="text-right text-xs text-zinc-500">
                    {formatSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{formatSize(row.tw_size)}
                  </TableCell>
                  <TableCell className="text-right"><span className="text-red-600 font-semibold text-sm">-${Math.abs(Number(row.gap)).toFixed(2)}</span></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Raise — IGA cheaper */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <ArrowUp className="h-4 w-4 text-emerald-500" /><h3 className="font-semibold text-emerald-600 dark:text-emerald-400">Raise These for More Margin</h3>
            <Badge variant="outline" className="text-emerald-600 border-emerald-300 dark:border-emerald-700 text-xs">IGA cheaper</Badge>
          </div>
          <Table>
            <TableHeader><TableRow>
              <TableHead>Product</TableHead>
              <TableHead className="text-right">IGA</TableHead>
              <TableHead className="text-right">TW</TableHead>
              <TableHead className="text-right w-14">Size</TableHead>
              <TableHead className="text-right">Gap</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {(raise.data || []).map((row: any, i: number) => (
                <TableRow key={i} className="bg-emerald-50/30 dark:bg-emerald-950/20">
                  <TableCell className="font-medium max-w-[180px] truncate">{row.name}</TableCell>
                  <TableCell className="text-right text-emerald-600 font-medium text-xs">{row.iga_display}</TableCell>
                  <TableCell className="text-right text-zinc-500 text-xs">{row.tw_display}</TableCell>
                  <TableCell className="text-right text-xs text-zinc-500">
                    {formatSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{formatSize(row.tw_size)}
                  </TableCell>
                  <TableCell className="text-right"><span className="text-emerald-600 font-semibold text-sm">+${Number(row.gap).toFixed(2)}</span></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
