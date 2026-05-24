"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ShoppingBasket, Trophy, AlertCircle } from "lucide-react";
import { useData } from "@/hooks/useData";

function fmtSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 14 ? s.substring(0, 14) : s;
}

export function StaplesTable() {
  const { data, isLoading } = useData("/api/staples");

  if (isLoading) {
    return (
      <Card><CardHeader><CardTitle>Staple Basket</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-96 w-full" /></CardContent></Card>
    );
  }

  const staples = (data || []).map((s: any) => {
    const igaPrice = Number(s.iga_price);
    const twPrice = Number(s.tw_price);
    const gap = igaPrice && twPrice ? twPrice - igaPrice : null;
    return { ...s, gap };
  });

  const igaTotal = staples.reduce((sum: number, s: any) => sum + (Number(s.iga_price) || 0), 0);
  const twTotal = staples.reduce((sum: number, s: any) => sum + (Number(s.tw_price) || 0), 0);
  const basketGap = twTotal - igaTotal;
  const igaWins = staples.filter((s: any) => s.gap > 0).length;
  const igaLosses = staples.filter((s: any) => s.gap < 0).length;

  return (
    <Card className="border-purple-200 dark:border-purple-500/10">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-purple-50 dark:bg-purple-500/10 flex items-center justify-center">
              <ShoppingBasket className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Staple Basket</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                <Trophy className="h-3 w-3 inline text-emerald-500" /> {igaWins} wins · <AlertCircle className="h-3 w-3 inline text-red-500" /> {igaLosses} losses
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-sm">
              <span className="font-mono-data text-emerald-600 dark:text-emerald-400 font-semibold">${igaTotal.toFixed(2)}</span>
              <span className="text-muted-foreground">IGA</span>
            </div>
            <span className="text-muted-foreground">vs</span>
            <div className="flex items-center gap-1.5 text-sm">
              <span className="font-mono-data font-semibold">${twTotal.toFixed(2)}</span>
              <span className="text-muted-foreground">TW</span>
            </div>
            <Badge className={basketGap > 0
              ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 font-mono-data"
              : "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20 font-mono-data"}>
              {basketGap > 0 ? "SAVE" : "LOSE"} ${Math.abs(basketGap).toFixed(2)}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs text-muted-foreground font-medium">Item</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium">IGA</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium">TW</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium w-16">Size</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground font-medium w-24">Result</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {staples.map((row: any, i: number) => (
              <TableRow key={i} className="border-border hover:bg-muted/50 transition-colors">
                <TableCell className="font-medium text-sm">{row.iga_name || "—"}</TableCell>
                <TableCell className="text-right font-mono-data text-sm">{row.iga_display || "—"}</TableCell>
                <TableCell className="text-right font-mono-data text-sm text-muted-foreground">{row.tw_display || "—"}</TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">{fmtSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{fmtSize(row.tw_size)}</TableCell>
                <TableCell className="text-right">
                  {row.gap == null ? (<span className="text-muted-foreground text-xs">—</span>) :
                   row.gap > 0 ? (<Badge className="bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 font-mono-data text-xs">WIN +${row.gap.toFixed(2)}</Badge>) :
                   row.gap < 0 ? (<Badge className="bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20 font-mono-data text-xs">-${Math.abs(row.gap).toFixed(2)}</Badge>) :
                   (<Badge variant="outline" className="text-muted-foreground text-xs">TIE</Badge>)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
