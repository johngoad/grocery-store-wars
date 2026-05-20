import { NextResponse } from "next/server";
import { getPriceGapDistribution } from "@/db/queries";

interface Bucket {
  bucket: string;
  count: number;
}

export async function GET() {
  const dbRows = (await getPriceGapDistribution()) as unknown as Bucket[];

  // Compute gaps array for binned histogram (approximation from buckets)
  const gaps: number[] = [];
  const bucketDefs: Record<string, { min: number; max: number; label: string }> = {
    iga_cheaper_20plus: { min: -50, max: -20, label: "cheaper" },
    iga_cheaper_10_20: { min: -20, max: -10, label: "cheaper" },
    iga_cheaper_2_10: { min: -10, max: -2, label: "cheaper" },
    near_parity: { min: -2, max: 2, label: "parity" },
    iga_pricier_2_10: { min: 2, max: 10, label: "pricier" },
    iga_pricier_10_20: { min: 10, max: 20, label: "pricier" },
    iga_pricier_20plus: { min: 20, max: 50, label: "pricier" },
  };

  let total = 0;
  let cheaper = 0;
  let parity = 0;
  let pricier = 0;

  for (const row of dbRows) {
    const def = bucketDefs[row.bucket];
    if (!def) continue;
    const midPoint = (def.min + def.max) / 2;
    for (let i = 0; i < row.count; i++) {
      gaps.push(midPoint);
    }
    total += row.count;
    if (def.label === "cheaper") cheaper += row.count;
    else if (def.label === "parity") parity += row.count;
    else pricier += row.count;
  }

  return NextResponse.json({
    gaps,
    summary: { total, cheaper, parity, pricier },
  });
}
