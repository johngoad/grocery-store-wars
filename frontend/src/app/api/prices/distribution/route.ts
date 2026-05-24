import { NextResponse } from "next/server";
import { getPriceGapDistribution } from "@/db/queries";
import { getCached, setCache, CACHE_5MIN } from "@/lib/cache";

export async function GET() {
  const key = "price-distribution";
  const cached = getCached(key);
  if (cached) return NextResponse.json(cached, { headers: CACHE_5MIN });

  const rows = await getPriceGapDistribution();
  const gaps: number[] = [];
  let cheaper = 0, parity = 0, pricier = 0;

  for (const r of rows as any[]) {
    if (r.bucket.startsWith("iga_cheaper")) cheaper += r.count;
    else if (r.bucket === "near_parity") parity += r.count;
    else pricier += r.count;
  }

  const data = {
    gaps,
    summary: { total: cheaper + parity + pricier, cheaper, parity, pricier },
  };

  setCache(key, data, 300);
  return NextResponse.json(data, { headers: CACHE_5MIN });
}
