import { NextResponse } from "next/server";
import { getStapleItems } from "@/db/queries";
import { getCached, setCache, CACHE_5MIN } from "@/lib/cache";

export async function GET() {
  const key = "staples";
  const cached = getCached(key);
  if (cached) return NextResponse.json(cached, { headers: CACHE_5MIN });

  const data = await getStapleItems();
  setCache(key, data, 300);
  return NextResponse.json(data, { headers: CACHE_5MIN });
}
