"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

interface ProductRow {
  name: string;
  iga_price: number;
  iga_display: string;
  iga_size: string | null;
  iga_size_oz: number | null;
  tw_name: string;
  tw_price: number;
  tw_display: string;
  tw_size: string | null;
  tw_size_oz: number | null;
  gap: number;
  gap_pct: number;
  size_diff: number | null;
  confidence: number;
  match_quality: string;
}

type SortKey = "name" | "iga_price" | "tw_price" | "gap" | "gap_pct" | "size_diff" | "confidence";

function formatSize(s: string | null) {
  if (!s || s === "each" || s === "per lb") return "";
  return s.length > 14 ? s.substring(0, 14) : s;
}

export default function DepartmentPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string || "";
  const deptName = slug.charAt(0).toUpperCase() + slug.slice(1);

  const [data, setData] = useState<ProductRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("gap");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    fetch(`/api/departments/${slug}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((rows: ProductRow[]) => { setData(rows); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, [slug]);

  const sorted = useMemo(() => {
    const dir = sortDir === "asc" ? 1 : -1;
    return [...data].sort((a: any, b: any) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (typeof av === "string") return dir * av.localeCompare(bv);
      return dir * (Number(av) - Number(bv));
    });
  }, [data, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("desc"); }
  };

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <ArrowUpDown className="h-3 w-3 inline ml-1 opacity-30" />;
    return sortDir === "asc" ? <ArrowUp className="h-3 w-3 inline ml-1" /> : <ArrowDown className="h-3 w-3 inline ml-1" />;
  };

  const Th = ({ col, label }: { col: SortKey; label: string }) => (
    <TableHead className="text-right cursor-pointer select-none hover:text-zinc-300" onClick={() => toggleSort(col)}>
      {label}<SortIcon col={col} />
    </TableHead>
  );

  if (loading) return <div className="min-h-screen bg-zinc-950 p-8"><Skeleton className="h-96 w-full" /></div>;
  if (error) return <div className="min-h-screen bg-zinc-950 p-8 text-red-400">Error: {error}</div>;

  const igaCheaper = sorted.filter(r => Number(r.gap) > 0).length;
  const igaPricier = sorted.filter(r => Number(r.gap) < 0).length;
  const sizeDisputes = sorted.filter(r => r.size_diff !== null && r.size_diff > 0.2).length;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-4">
          <button onClick={() => router.push("/")} className="p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-zinc-900 dark:text-white">{deptName} Department</h1>
            <p className="text-xs text-zinc-500">
              {sorted.length} products · {igaCheaper} IGA cheaper · {igaPricier} IGA pricier
              {sizeDisputes > 0 && ` · ${sizeDisputes} size mismatches`}
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Product Price Comparison</CardTitle>
            <p className="text-xs text-zinc-500">Click column headers to sort. Size mismatches flagged in amber.</p>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="cursor-pointer select-none hover:text-zinc-300" onClick={() => toggleSort("name")}>
                    Product<SortIcon col="name" />
                  </TableHead>
                  <Th col="iga_price" label="IGA" />
                  <Th col="tw_price" label="Thriftway" />
                  <TableHead className="text-right text-xs">Size</TableHead>
                  <Th col="gap" label="Gap $" />
                  <Th col="gap_pct" label="Gap %" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {sorted.map((row, i) => {
                  const gap = Number(row.gap);
                  const igaIsCheaper = gap > 0;
                  const sizeIssue = row.size_diff !== null && row.size_diff > 0.2;
                  const isMismatch = row.match_quality === "size_mismatch";

                  return (
                    <TableRow key={i} className={
                      isMismatch ? "opacity-40" :
                      sizeIssue ? "bg-amber-50/30 dark:bg-amber-950/10" :
                      igaIsCheaper ? "bg-emerald-50/30 dark:bg-emerald-950/10" :
                      "bg-red-50/30 dark:bg-red-950/10"
                    }>
                      <TableCell className="font-medium text-xs max-w-[250px] truncate" title={row.name}>
                        {row.name}
                        {isMismatch && <Badge variant="outline" className="ml-2 text-[10px] text-red-500 border-red-300">size</Badge>}
                        {sizeIssue && !isMismatch && <Badge variant="outline" className="ml-2 text-[10px] text-amber-500 border-amber-300">size?</Badge>}
                      </TableCell>
                      <TableCell className="text-right text-xs font-medium">
                        <span className={igaIsCheaper ? "text-emerald-600" : "text-red-600"}>{row.iga_display}</span>
                      </TableCell>
                      <TableCell className="text-right text-xs text-zinc-500">{row.tw_display}</TableCell>
                      <TableCell className="text-right text-[10px] text-zinc-500">
                        {formatSize(row.iga_size)}{row.iga_size && row.tw_size && " / "}{formatSize(row.tw_size)}
                      </TableCell>
                      <TableCell className="text-right text-xs font-semibold">
                        <span className={igaIsCheaper ? "text-emerald-600" : "text-red-600"}>
                          {igaIsCheaper ? "+" : "-"}${Math.abs(gap).toFixed(2)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-xs">
                        <span className={igaIsCheaper ? "text-emerald-500" : "text-red-500"}>
                          {igaIsCheaper ? "+" : ""}{Number(row.gap_pct).toFixed(1)}%
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
