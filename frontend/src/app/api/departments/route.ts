import { NextResponse } from "next/server";
import { getDepartmentComparison } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const deptId = searchParams.get("id");
  const results = await getDepartmentComparison(deptId || undefined);
  return NextResponse.json(results, { headers: { "Cache-Control": "public, max-age=60, stale-while-revalidate=300" } });
}
