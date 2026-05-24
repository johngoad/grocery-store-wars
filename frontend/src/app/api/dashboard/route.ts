import { NextResponse } from "next/server";
import { getDashboardStats } from "@/db/queries";
import { getCached, setCache, CACHE_5MIN } from "@/lib/cache";

export async function GET() {
  const key = "dashboard";
  const cached = getCached(key);
  if (cached) return NextResponse.json(cached, { headers: CACHE_5MIN });

  const stats = await getDashboardStats();
  const data = { stats };
  setCache(key, data, 300);
  return NextResponse.json(data, { headers: CACHE_5MIN });
}
