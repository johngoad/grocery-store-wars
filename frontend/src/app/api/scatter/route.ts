import { NextResponse } from "next/server";
import { getScatterData } from "@/db/queries";

export async function GET() {
  const results = await getScatterData();
  return NextResponse.json(results, {
    headers: { "Cache-Control": "public, max-age=120, stale-while-revalidate=300" }
  });
}
