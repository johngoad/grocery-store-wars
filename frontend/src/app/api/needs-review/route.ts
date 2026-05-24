import { NextResponse } from "next/server";
import turso from "@/db";
import { getCached, setCache, CACHE_5MIN } from "@/lib/cache";

export async function GET() {
  const key = "needs-review";
  const cached = getCached(key);
  if (cached) return NextResponse.json(cached, { headers: CACHE_5MIN });

  const result = await turso.execute(`
    SELECT p.name, p.price as iga_price, p.price_display as iga_display, p.size as iga_size,
      pt_comp.price as tw_price, pt_comp.price_display as tw_display,
      ROUND(ABS(p.price - pt_comp.price), 2) as gap,
      pm.match_quality
    FROM products p
    JOIN product_matches pm ON p.id = pm.iga_product_id
    JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
    WHERE p.store_id = 'iga-vashon'
      AND p.price IS NOT NULL AND pt_comp.price IS NOT NULL
      AND pm.match_quality != 'size_mismatch'
      AND p.size_oz IS NOT NULL AND pt_comp.size_oz IS NOT NULL
      AND ABS(p.size_oz - pt_comp.size_oz) < 0.2 * CASE WHEN p.size_oz > pt_comp.size_oz THEN p.size_oz ELSE pt_comp.size_oz END
      AND ABS(p.price - pt_comp.price) > 3
    ORDER BY ABS(p.price - pt_comp.price) DESC
    LIMIT 50
  `);

  setCache(key, result.rows, 300);
  return NextResponse.json(result.rows, { headers: CACHE_5MIN });
}
