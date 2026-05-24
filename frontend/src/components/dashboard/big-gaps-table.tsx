"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ArrowDown, ArrowUp } from "lucide-react";
import { useData } from "@/hooks/useData";

function formatSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 14 ? s.substring(0, 14) : s;
}

export function BigGapsTable() {
  const undercut = useData("/api/margins?limit=10&direction=undercut");
  const raise = useData("/api/margins?limit=10&direction=raise");
  const isLoading = undercut.isLoading || raise.isLoading;

  if (isLoading) {
    return (
      <Card><CardHeader><CardTitle>Big Price Gaps</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-96 w-full" /></CardContent></Card>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* IGA Pricier */}
      <Card className="border-red-200 dark:border-red-500/10">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-red-50 dark:bg-red-500/10 flex items-center justify-center">
              <ArrowDown className="h-4 w-4 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Lower These Prices</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">IGA is above market — consider reducing</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-xs text-muted-foreground font-medium">Product</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium">IGA</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium">TW</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium w-16">Size</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium">Gap</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(undercut.data || []).map((row: any, i: number) => (
                <TableRow key={i} className="border-border hover:bg-red-50/50 dark:hover:bg-red-500/5 transition-colors">
                  <TableCell className="font-medium text-sm max-w-[160px] truncate">{row.name}</TableCell>
                  <TableCell className="text-right text-red-600 dark:text-red-400 font-mono-data text-sm">{row.iga_display}</TableCell>
                  <TableCell className="text-right text-muted-foreground font-mono-data text-sm">{row.tw_display}</TableCell>
                  <TableCell className="text-right text-xs text-muted-foreground">
                    {formatSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{formatSize(row.tw_size)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="outline" className="bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/20 font-mono-data text-xs">
                      +${Math.abs(Number(row.gap)).toFixed(2)}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
              {(!undercut.data || undercut.data.length === 0) && (
                <TableRow className="border-border"><TableCell colSpan={5} className="text-center text-muted-foreground py-8">No items found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* IGA Cheaper */}
      <Card className="border-emerald-200 dark:border-emerald-500/10">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center">
              <ArrowUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Raise These for Margin</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">IGA is below market — room to increase</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-xs text-muted-foreground font-medium">Product</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium">IGA</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium">TW</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium w-16">Size</TableHead>
                <TableHead className="text-right text-xs text-muted-foreground font-medium">Gap</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(raise.data || []).map((row: any, i: number) => (
                <TableRow key={i} className="border-border hover:bg-emerald-50/50 dark:hover:bg-emerald-500/5 transition-colors">
                  <TableCell className="font-medium text-sm max-w-[160px] truncate">{row.name}</TableCell>
                  <TableCell className="text-right text-emerald-600 dark:text-emerald-400 font-mono-data text-sm">{row.iga_display}</TableCell>
                  <TableCell className="text-right text-muted-foreground font-mono-data text-sm">{row.tw_display}</TableCell>
                  <TableCell className="text-right text-xs text-muted-foreground">
                    {formatSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{formatSize(row.tw_size)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="outline" className="bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20 font-mono-data text-xs">
                      +${Number(row.gap).toFixed(2)}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
              {(!raise.data || raise.data.length === 0) && (
                <TableRow className="border-border"><TableCell colSpan={5} className="text-center text-muted-foreground py-8">No items found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
