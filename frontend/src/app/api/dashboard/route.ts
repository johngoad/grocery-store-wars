import { NextResponse } from "next/server";
import { getDashboardStats } from "@/db/queries";

export async function GET() {
  const stats = await getDashboardStats();
  return NextResponse.json({ stats }, { headers: { "Cache-Control": "public, max-age=60, stale-while-revalidate=300" } });
}
