import { NextResponse } from "next/server";
import { getDashboardStats, getStapleItems, getMarginOpportunities } from "@/db/queries";

export async function GET() {
  const stats = await getDashboardStats();
  const staples = await getStapleItems();
  const margins = await getMarginOpportunities(10);

  return NextResponse.json({ stats, staples, margins });
}
