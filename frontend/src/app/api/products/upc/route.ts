import { NextResponse } from "next/server";
import { lookupByUPC } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const upc = searchParams.get("code");
  if (!upc) return NextResponse.json({ error: "Missing code parameter" }, { status: 400 });

  const results = await lookupByUPC(upc);
  return NextResponse.json(results);
}
