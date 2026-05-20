"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { TrendingUp } from "lucide-react";
import { useData } from "@/hooks/useData";

function fmtSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 12 ? s.substring(0, 12) : s;
}

export function MarginTable() {
  const { data, isLoading } = useData("/api/margins?limit=20&direction=raise");

  if (isLoading) {
    return <Card><CardHeader><CardTitle>Margin Opportunities</CardTitle></CardHeader><CardContent><Skeleton className="h-80 w-full" /></CardContent></Card>;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-emerald-500" />Margin Opportunities</CardTitle>
          <Badge variant="outline" className="text-emerald-600 border-emerald-300 dark:border-emerald-700">Raise + still win</Badge>
        </div>
        <p className="text-sm text-zinc-500">IGA cheaper — raise prices while staying below Thriftway. Sizes verified.</p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader><TableRow>
            <TableHead>Product</TableHead><TableHead className="text-right">IGA</TableHead><TableHead className="text-right">TW</TableHead>
            <TableHead className="text-right w-14">Size</TableHead><TableHead className="text-right">Gap</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {(data || []).map((row: any, i: number) => (
              <TableRow key={i}>
                <TableCell className="font-medium max-w-[180px] truncate">{row.name}</TableCell>
                <TableCell className="text-right text-emerald-600 font-medium text-xs">{row.iga_display}</TableCell>
                <TableCell className="text-right text-zinc-500 text-xs">{row.tw_display}</TableCell>
                <TableCell className="text-right text-xs text-zinc-500">{fmtSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{fmtSize(row.tw_size)}</TableCell>
                <TableCell className="text-right"><span className="text-emerald-600 font-medium">+${Number(row.gap).toFixed(2)}</span></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
