import { NextResponse } from "next/server";
import turso from "@/db";

const IGA_STORE = "iga-vashon";

export async function GET() {
  const result = await turso.execute({
    sql: `
      SELECT p.name, p.price as iga_price, p.price_display as iga_display, p.size as iga_size,
        pt_comp.name as tw_name, pt_comp.price as tw_price, pt_comp.price_display as tw_display, pt_comp.size as tw_size,
        ROUND(ABS(p.price - pt_comp.price), 2) as gap,
        CASE WHEN p.price < pt_comp.price THEN 'raise' ELSE 'undercut' END as direction
      FROM products p
      JOIN product_matches pm ON p.id = pm.iga_product_id
      JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
      WHERE p.store_id = ?
        AND p.price IS NOT NULL
        AND pt_comp.price IS NOT NULL
        AND pm.match_quality != 'size_mismatch'
        AND p.size_oz IS NOT NULL AND pt_comp.size_oz IS NOT NULL
        AND ABS(p.size_oz - pt_comp.size_oz) < 0.2 * CASE WHEN p.size_oz > pt_comp.size_oz THEN p.size_oz ELSE pt_comp.size_oz END
        AND ABS(p.price - pt_comp.price) > 3
      ORDER BY ABS(p.price - pt_comp.price) DESC
    `,
    args: [IGA_STORE],
  });
  return NextResponse.json(result.rows, { headers: { "Cache-Control": "public, max-age=60, stale-while-revalidate=300" } });
}
