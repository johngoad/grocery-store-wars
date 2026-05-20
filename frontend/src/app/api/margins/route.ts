import { NextResponse } from "next/server";
import { getMarginOpportunities } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "20");
  const direction = (searchParams.get("direction") || "raise") as "raise" | "undercut";
  const results = await getMarginOpportunities(limit, direction);
  return NextResponse.json(results);
}
