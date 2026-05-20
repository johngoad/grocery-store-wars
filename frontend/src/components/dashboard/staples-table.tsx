"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ShoppingBasket } from "lucide-react";
import { useData } from "@/hooks/useData";

function fmtSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 12 ? s.substring(0, 12) : s;
}

export function StaplesTable() {
  const { data, isLoading } = useData("/api/staples");

  if (isLoading) {
    return <Card><CardHeader><CardTitle>Staple Basket</CardTitle></CardHeader><CardContent><Skeleton className="h-96 w-full" /></CardContent></Card>;
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
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="flex items-center gap-2"><ShoppingBasket className="h-5 w-5" />Staple Basket</CardTitle>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-emerald-600 font-semibold">IGA: ${igaTotal.toFixed(2)}</span>
            <span className="text-zinc-300 dark:text-zinc-700">|</span>
            <span className="text-zinc-500">TW: ${twTotal.toFixed(2)}</span>
            <span className="text-zinc-300 dark:text-zinc-700">|</span>
            <Badge className={basketGap > 0 ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400" : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400"}>
              {basketGap > 0 ? "SAVE" : "LOSE"} ${Math.abs(basketGap).toFixed(2)}
            </Badge>
          </div>
        </div>
        <p className="text-sm text-zinc-500">{igaWins} wins · {igaLosses} losses · {staples.length} staples</p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader><TableRow>
            <TableHead>Item</TableHead><TableHead className="text-right">IGA</TableHead><TableHead className="text-right">TW</TableHead>
            <TableHead className="text-right w-14">Size</TableHead><TableHead className="text-right w-24">Result</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {staples.map((row: any, i: number) => (
              <TableRow key={i}>
                <TableCell className="font-medium text-xs">{row.iga_name || "—"}</TableCell>
                <TableCell className="text-right text-xs">{row.iga_display || "—"}</TableCell>
                <TableCell className="text-right text-xs">{row.tw_display || "—"}</TableCell>
                <TableCell className="text-right text-xs text-zinc-500">{fmtSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{fmtSize(row.tw_size)}</TableCell>
                <TableCell className="text-right">
                  {row.gap == null ? (<span className="text-zinc-400 text-xs">—</span>) :
                   row.gap > 0 ? (<Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400 text-xs">WIN +${row.gap.toFixed(2)}</Badge>) :
                   row.gap < 0 ? (<Badge className="bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400 text-xs">-${Math.abs(row.gap).toFixed(2)}</Badge>) :
                   (<Badge variant="outline" className="text-xs">TIE</Badge>)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
