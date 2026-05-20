import { NextResponse } from "next/server";
import { searchProducts } from "@/db/queries";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q");
  if (!q) return NextResponse.json({ error: "Missing q parameter" }, { status: 400 });

  const results = await searchProducts(q);
  return NextResponse.json(results);
}
