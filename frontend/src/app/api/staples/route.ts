import { NextResponse } from "next/server";
import { getStapleItems } from "@/db/queries";

export async function GET() {
  const results = await getStapleItems();
  return NextResponse.json(results, { headers: { "Cache-Control": "public, max-age=60, stale-while-revalidate=300" } });
}
