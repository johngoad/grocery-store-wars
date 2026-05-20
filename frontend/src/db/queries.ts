import turso from "./index";

const IGA_STORE = "iga-vashon";
const TW_STORE = "thriftway-vashon";

// Size parity: require BOTH products have extractable sizes and they match within 20%
const SIZE_PARITY = `p.size_oz IS NOT NULL AND pt_comp.size_oz IS NOT NULL AND 
     ABS(p.size_oz - pt_comp.size_oz) < 0.2 * CASE WHEN p.size_oz > pt_comp.size_oz THEN p.size_oz ELSE pt_comp.size_oz END`;

// --- Dashboard Stats ---
export async function getDashboardStats() {
  const result = await turso.execute(`
    SELECT
      (SELECT COUNT(*) FROM products WHERE store_id = '${IGA_STORE}') as iga_count,
      (SELECT COUNT(*) FROM products WHERE store_id = '${TW_STORE}') as tw_count,
      (SELECT COUNT(*) FROM product_matches WHERE match_quality != 'size_mismatch') as matched_count,
      (SELECT ROUND(AVG(p.price - pt_comp.price), 2)
       FROM product_matches pm
       JOIN products p ON pm.iga_product_id = p.id
       JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
       WHERE p.price IS NOT NULL AND pt_comp.price IS NOT NULL
         AND pm.match_quality != 'size_mismatch'
         AND ${SIZE_PARITY}) as avg_price_gap
  `);
  return result.rows[0];
}

// --- Staple Items ---
export async function getStapleItems() {
  const result = await turso.execute(`
    SELECT si.*,
      ps.name as iga_name, ps.price as iga_price, ps.price_display as iga_display, ps.size as iga_size,
      pt_comp.name as tw_name, pt_comp.price as tw_price, pt_comp.price_display as tw_display, pt_comp.size as tw_size
    FROM staple_items si
    LEFT JOIN products ps ON si.iga_product_id = ps.id
    LEFT JOIN products pt_comp ON si.thriftway_product_id = pt_comp.id
    ORDER BY si.display_order
    LIMIT 50
  `);
  return result.rows;
}

// --- Product Search ---
export async function searchProducts(query: string, limit = 20) {
  const result = await turso.execute({
    sql: `
      SELECT p.*, pm.thriftway_product_id, pm.confidence as match_confidence,
        pt_comp.price as competitor_price, pt_comp.price_display as competitor_display,
        pt_comp.name as competitor_name
      FROM products p
      LEFT JOIN product_matches pm ON p.id = pm.iga_product_id
      LEFT JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
      WHERE p.store_id = ? AND p.name LIKE ?
      ORDER BY p.name
      LIMIT ?
    `,
    args: [IGA_STORE, `%${query}%`, limit],
  });
  return result.rows;
}

// --- UPC Lookup ---
export async function lookupByUPC(upc: string) {
  const result = await turso.execute({
    sql: `
      SELECT p.*, pm.thriftway_product_id, pm.match_type, pm.confidence,
        pt_comp.price as competitor_price, pt_comp.price_display as competitor_display,
        pt_comp.name as competitor_name
      FROM products p
      LEFT JOIN product_matches pm ON p.id = pm.iga_product_id
      LEFT JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
      WHERE (p.upc = ? OR p.barcode = ?)
      LIMIT 5
    `,
    args: [upc, upc],
  });
  return result.rows;
}

// --- Department Comparison ---
export async function getDepartmentComparison(departmentId?: string) {
  let sql = `
    SELECT p.department_id, d.name as department_name,
      COUNT(*) as product_count,
      ROUND(AVG(p.price), 2) as avg_iga_price,
      ROUND(AVG(pt_comp.price), 2) as avg_tw_price,
      ROUND(AVG(p.price - pt_comp.price), 2) as avg_gap
    FROM products p
    JOIN product_matches pm ON p.id = pm.iga_product_id
    JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
    LEFT JOIN departments d ON p.department_id = d.id
    WHERE p.store_id = '${IGA_STORE}' AND p.price IS NOT NULL AND pt_comp.price IS NOT NULL
      AND pm.match_quality != 'size_mismatch'
      AND ${SIZE_PARITY}
  `;
  if (departmentId) {
    sql += ` AND p.department_id = '${departmentId}'`;
  }
  sql += ` GROUP BY p.department_id ORDER BY product_count DESC`;
  const result = await turso.execute(sql);
  return result.rows;
}

// --- Margin Opportunities ---
export async function getMarginOpportunities(limit = 10, direction: "raise" | "undercut" = "raise") {
  const isRaise = direction === "raise";
  const result = await turso.execute({
    sql: `
      SELECT p.name, p.price as iga_price, p.price_display as iga_display, p.size as iga_size,
        pt_comp.price as tw_price, pt_comp.price_display as tw_display, pt_comp.size as tw_size,
        ROUND(pt_comp.price - p.price, 2) as gap,
        ROUND(pt_comp.price - 0.05, 2) as suggested_price,
        pm.match_quality
      FROM products p
      JOIN product_matches pm ON p.id = pm.iga_product_id
      JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
      WHERE p.store_id = ?
        AND p.price IS NOT NULL
        AND pt_comp.price IS NOT NULL
        AND pm.match_quality != 'size_mismatch'
        AND ${SIZE_PARITY}
        AND ${isRaise ? "p.price < pt_comp.price" : "p.price > pt_comp.price"}
      ORDER BY ${isRaise ? "(pt_comp.price - p.price) DESC" : "(p.price - pt_comp.price) DESC"}
      LIMIT ?
    `,
    args: [IGA_STORE, limit],
  });
  return result.rows;
}

// --- Price Gap Distribution ---
export async function getPriceGapDistribution() {
  const result = await turso.execute({
    sql: `
      SELECT
        CASE
          WHEN p.price <= pt_comp.price * 0.80 THEN 'iga_cheaper_20plus'
          WHEN p.price <= pt_comp.price * 0.90 THEN 'iga_cheaper_10_20'
          WHEN p.price <= pt_comp.price * 0.98 THEN 'iga_cheaper_2_10'
          WHEN ABS(p.price - pt_comp.price) / pt_comp.price <= 0.02 THEN 'near_parity'
          WHEN p.price <= pt_comp.price * 1.10 THEN 'iga_pricier_2_10'
          WHEN p.price <= pt_comp.price * 1.20 THEN 'iga_pricier_10_20'
          ELSE 'iga_pricier_20plus'
        END as bucket,
        COUNT(*) as count
      FROM products p
      JOIN product_matches pm ON p.id = pm.iga_product_id
      JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
      WHERE p.store_id = ?
        AND p.price > 0
        AND pt_comp.price > 0
        AND pm.match_quality != 'size_mismatch'
        AND ${SIZE_PARITY}
      GROUP BY bucket
      ORDER BY bucket
    `,
    args: [IGA_STORE],
  });
  return result.rows;
}

// --- Price History ---
export async function getPriceHistory(productId: string, days = 30) {
  const result = await turso.execute({
    sql: `
      SELECT ph.*, s.name as store_name
      FROM price_history ph
      JOIN stores s ON ph.store_id = s.id
      WHERE ph.product_id = ?
        AND ph.recorded_at >= datetime('now', ? || ' days')
      ORDER BY ph.recorded_at DESC
      LIMIT 100
    `,
    args: [productId, `-${days}`],
  });
  return result.rows;
}
