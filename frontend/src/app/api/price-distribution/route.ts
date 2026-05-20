import { NextResponse } from "next/server";
import turso from "@/db/index";

const IGA_STORE = "iga-vashon";

export async function GET() {
  const result = await turso.execute(`
    SELECT
      CASE
        WHEN (p.price - pt_comp.price) <= -2.00 THEN 'iga_2plus_cheaper'
        WHEN (p.price - pt_comp.price) <= -1.00 THEN 'iga_1to2_cheaper'
        WHEN (p.price - pt_comp.price) <= -0.50 THEN 'iga_50ct_1_cheaper'
        WHEN (p.price - pt_comp.price) <= -0.10 THEN 'iga_10ct_50ct_cheaper'
        WHEN (p.price - pt_comp.price) BETWEEN -0.10 AND 0.10 THEN 'within_10ct'
        WHEN (p.price - pt_comp.price) BETWEEN 0.10 AND 0.50 THEN 'tw_10ct_50ct_cheaper'
        WHEN (p.price - pt_comp.price) BETWEEN 0.50 AND 1.00 THEN 'tw_50ct_1_cheaper'
        WHEN (p.price - pt_comp.price) BETWEEN 1.00 AND 2.00 THEN 'tw_1to2_cheaper'
        ELSE 'tw_2plus_cheaper'
      END as range,
      CASE
        WHEN (p.price - pt_comp.price) <= -2.00 THEN 'IGA $2+ cheaper'
        WHEN (p.price - pt_comp.price) <= -1.00 THEN 'IGA $1-2 cheaper'
        WHEN (p.price - pt_comp.price) <= -0.50 THEN 'IGA $0.50-1 cheaper'
        WHEN (p.price - pt_comp.price) <= -0.10 THEN 'IGA $0.10-0.50 cheaper'
        WHEN (p.price - pt_comp.price) BETWEEN -0.10 AND 0.10 THEN 'Within $0.10'
        WHEN (p.price - pt_comp.price) BETWEEN 0.10 AND 0.50 THEN 'TW $0.10-0.50 cheaper'
        WHEN (p.price - pt_comp.price) BETWEEN 0.50 AND 1.00 THEN 'TW $0.50-1 cheaper'
        WHEN (p.price - pt_comp.price) BETWEEN 1.00 AND 2.00 THEN 'TW $1-2 cheaper'
        ELSE 'TW $2+ cheaper'
      END as label,
      CASE
        WHEN (p.price - pt_comp.price) <= -0.10 THEN 'green'
        WHEN (p.price - pt_comp.price) BETWEEN -0.10 AND 0.10 THEN 'amber'
        ELSE 'red'
      END as color,
      COUNT(*) as count
    FROM products p
    JOIN product_matches pm ON p.id = pm.iga_product_id
    JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
    WHERE p.store_id = '${IGA_STORE}'
      AND p.price IS NOT NULL
      AND pt_comp.price IS NOT NULL
      AND pm.match_quality != 'size_mismatch'
    GROUP BY range, label, color
    ORDER BY MIN(p.price - pt_comp.price) ASC
  `);

  return NextResponse.json(result.rows);
}
