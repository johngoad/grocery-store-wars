"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { TrendingUp } from "lucide-react";
import { useData } from "@/hooks/useData";

function fmtSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 14 ? s.substring(0, 14) : s;
}

export function MarginTable() {
  const { data, isLoading } = useData("/api/margins?limit=20&direction=raise");

  if (isLoading) {
    return (
      <Card><CardHeader><CardTitle>Margin Opportunities</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-80 w-full" /></CardContent></Card>
    );
  }

  return (
    <Card className="border-amber-200 dark:border-amber-500/10">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-amber-50 dark:bg-amber-500/10 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Margin Opportunities</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">IGA is cheaper — room to raise and still beat Thriftway</p>
            </div>
          </div>
          <Badge variant="outline" className="bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-500/20 text-xs">
            Raise + still win
          </Badge>
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
            {(data || []).map((row: any, i: number) => (
              <TableRow key={i} className="border-border hover:bg-amber-50/50 dark:hover:bg-amber-500/5 transition-colors">
                <TableCell className="font-medium text-sm max-w-[200px] truncate">{row.name}</TableCell>
                <TableCell className="text-right font-mono-data text-sm text-amber-600 dark:text-amber-400">{row.iga_display}</TableCell>
                <TableCell className="text-right font-mono-data text-sm text-muted-foreground">{row.tw_display}</TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">{fmtSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{fmtSize(row.tw_size)}</TableCell>
                <TableCell className="text-right">
                  <Badge className="bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20 font-mono-data text-xs">
                    +${Number(row.gap).toFixed(2)}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
