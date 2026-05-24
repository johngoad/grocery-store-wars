"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, ZAxis,
} from "recharts";
import { useData } from "@/hooks/useData";
import { Crosshair, TrendingUp, TrendingDown } from "lucide-react";

const DEPT_COLORS: Record<string, string> = {
  Produce: "#10b981", Meat: "#ef4444", Dairy: "#3b82f6",
  "Dairy & Eggs": "#3b82f6", Bakery: "#f59e0b", Deli: "#8b5cf6",
  Grocery: "#6b7280", Frozen: "#06b6d4", Beverages: "#ec4899",
  "Beer & Wine": "#f97316", "Health & Beauty": "#84cc16",
};

function getColor(dept: string): string {
  for (const [key, color] of Object.entries(DEPT_COLORS)) {
    if (dept.includes(key)) return color;
  }
  return "#6b7280";
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload || !payload[0]) return null;
  const p = payload[0].payload;
  const gap = p.gap;
  const isIGACheaper = p.igaPrice < p.twPrice;
  const absGap = Math.abs(gap);

  return (
    <div style={{
      backgroundColor: "var(--popover)", border: "1px solid var(--border)",
      borderRadius: "12px", padding: "12px 14px", fontSize: "13px",
      color: "var(--popover-foreground)", boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
      minWidth: "220px",
    }}>
      <p style={{ fontWeight: 600, fontSize: "13px", marginBottom: "4px", lineHeight: 1.3 }}>
        {p.name}
      </p>
      <p style={{ fontSize: "11px", color: "var(--muted-foreground)", marginBottom: "8px" }}>
        {p.dept}
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "3px", marginBottom: "8px" }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "var(--muted-foreground)" }}>IGA</span>
          <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
            ${p.igaPrice.toFixed(2)}
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "var(--muted-foreground)" }}>Thriftway</span>
          <span style={{ fontFamily: "var(--font-mono)" }}>
            ${p.twPrice.toFixed(2)}
          </span>
        </div>
      </div>
      <div style={{
        display: "flex", alignItems: "center", gap: "6px",
        padding: "6px 10px", borderRadius: "8px",
        backgroundColor: isIGACheaper ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
        border: isIGACheaper ? "1px solid rgba(16,185,129,0.2)" : "1px solid rgba(239,68,68,0.2)",
      }}>
        {isIGACheaper ? (
          <TrendingUp style={{ width: 14, height: 14, color: "#10b981" }} />
        ) : (
          <TrendingDown style={{ width: 14, height: 14, color: "#ef4444" }} />
        )}
        <span style={{
          fontSize: "12px", fontWeight: 700,
          fontFamily: "var(--font-mono)",
          color: isIGACheaper ? "#10b981" : "#ef4444",
        }}>
          {isIGACheaper ? "Raise" : "Cut"} ${absGap.toFixed(2)}
        </span>
        <span style={{ fontSize: "11px", color: "var(--muted-foreground)" }}>
          {isIGACheaper ? "room to increase" : "above market"}
        </span>
      </div>
    </div>
  );
}

export function PositionMap() {
  const { data, isLoading } = useData("/api/scatter");

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Competitive Position Map</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-[420px] w-full" /></CardContent>
      </Card>
    );
  }

  const points = (data || []).map((d: any) => ({
    x: Number(d.iga_price),
    y: Number(d.tw_price),
    z: Math.max(Number(d.gap) * 8, 20),
    name: d.name,
    dept: d.department,
    gap: Number(d.gap),
    igaPrice: Number(d.iga_price),
    twPrice: Number(d.tw_price),
    fill: getColor(d.department),
  }));

  const maxPrice = Math.max(
    ...points.map((p: any) => Math.max(p.x, p.y)),
    20
  );

  const depts = ([...new Set(points.map((p: any) => p.dept))] as string[]).slice(0, 8);

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Crosshair className="h-4 w-4 text-emerald-500" />
          <CardTitle className="text-base font-semibold">Competitive Position Map</CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          Each dot = one product. Hover for name, price, and action.
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={380}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 30, left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis
              type="number" dataKey="x" name="IGA Price"
              domain={[0, maxPrice]}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              label={{ value: "IGA Price ($)", position: "bottom", offset: -5, style: { fill: "var(--muted-foreground)", fontSize: 11 } }}
            />
            <YAxis
              type="number" dataKey="y" name="Thriftway Price"
              domain={[0, maxPrice]}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              label={{ value: "Thriftway Price ($)", angle: -90, position: "left", style: { fill: "var(--muted-foreground)", fontSize: 11 } }}
            />
            <ZAxis type="number" dataKey="z" range={[20, 200]} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="var(--border)" strokeDasharray="3 3" />
            <ReferenceLine
              segment={[{ x: 0, y: 0 }, { x: maxPrice, y: maxPrice }]}
              stroke="#10b981" strokeOpacity={0.4} strokeWidth={2} strokeDasharray="6 4"
            />
            <Scatter data={points} fillOpacity={0.6} strokeOpacity={0.3}>
              {points.map((entry: any, index: number) => (
                <circle
                  key={index}
                  cx={0} cy={0} r={0}
                  fill={entry.fill}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 mt-3 pt-3 border-t border-border">
          {(depts as string[]).map((dept: string) => (
            <div key={dept} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getColor(dept) }} />
              {dept}
            </div>
          ))}
        </div>

        {/* Key */}
        <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-500/60" style={{ borderTop: "2px dashed #10b981" }} />
            Above line = IGA cheaper
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-red-400/60" />
            Below line = IGA pricier
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
