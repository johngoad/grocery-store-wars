import { NextResponse } from "next/server";
import { getMarginOpportunities } from "@/db/queries";
import { getCached, setCache, CACHE_5MIN } from "@/lib/cache";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "20");
  const direction = (searchParams.get("direction") || "raise") as "raise" | "undercut";
  
  const key = `margins-${direction}-${limit}`;
  const cached = getCached(key);
  if (cached) return NextResponse.json(cached, { headers: CACHE_5MIN });

  const data = await getMarginOpportunities(limit, direction);
  setCache(key, data, 300);
  return NextResponse.json(data, { headers: CACHE_5MIN });
}
