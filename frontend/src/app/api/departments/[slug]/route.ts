import { NextResponse } from "next/server";
import turso from "@/db";

// Strict department names — raw products only, no processed/canned/prepared
const DEPT_NAMES: Record<string, string[]> = {
  produce: [
    // Fresh fruits
    "Apple", "Apples", "Avocados", "Bananas & Plantains",
    "Berries & Cherries", "Blueberries", "Cherries",
    "Citrus", "Fruit", "Grape", "Grapes",
    "Melons", "Mixed Fruit", "Organic Fruits",
    "Organic Fruits & Vegetables", "Peaches", "Pears",
    "Pineapple", "Stone Fruit", "Strawberries",
    "Tropical & Specialty",
    // Fresh vegetables
    "Beets", "Broccoli", "Broccoli & Cauliflower",
    "Brussel Sprouts & Cabbage", "Carrots", "Carrots & Beets",
    "Cauliflower", "Celery", "Corn", "Cucumbers",
    "Fresh Herbs", "Green", "Leafy Greens", "Lettuce",
    "Mushroom", "Mushrooms", "Okra",
    "Onions", "Onions & Garlic",
    "Organic Vegetables", "Peppers", "Peppers & Chilis",
    "Potato", "Potatoes", "Potatoes & Yams",
    "Produce", "Pumpkin", "Radishes",
    "Root Vegetables & Tropical Roots",
    "Squash & Zucchini", "Tomato", "Tomatoes",
    "Vegetable", "Vegetable & Tomato", "Vegetables", "Veggie",
    // Fresh herbs
    "Mixed Vegetables",
  ],
  meat: [
    // Fresh beef
    "Beef", "Beef & Veal", "Beef Roasts & Ribs",
    "Ground Beef & Burgers", "Burger, Ground Meat",
    "Steaks & Fillets", "Specialty Cuts",
    "Kabobs, Stew, Cubes & Strips",
    // Fresh pork
    "Pork", "Pork Roasts", "Chops & Ribs",
    "Ham", "Loins",
    // Fresh poultry
    "Chicken", "Chicken Breasts",
    "Chicken Legs, Thighs & Wings", "Whole Chicken",
    "Turkey", "Ground Chicken", "Ground Turkey & Burgers",
    "Poultry", "Wings",
    // Fresh lamb/other
    "Lamb & Veal", "Ground Meat", "Ground Pork",
    "Meat", "Meat, Seafood & Poultry",
    // Fresh sausage (raw, not cured)
    "Brat", "Brats & Sausages", "Sausage", "Sausages",
    "Kielbasa",
    // Bacon (fresh)
    "Bacon",
  ],
  dairy: [
    // Milk
    "1% Milk", "2% Milk", "Whole Milk", "Milk", "Milk & Cream",
    "Skim & Nonfat", "Lactose Free",
    "Almond Milk", "Coconut Milk", "Soy Milk", "Rice Milk",
    "Milk Alternatives", "Dry Milk", "Powdered Milk",
    "Evaporated Milk, Condensed Milk & Powdered Milk",
    // Cheese
    "Cheese", "Cheddar", "Colby", "Monterey Jack",
    "Mozzarella & Ricotta", "Parmesan & Romano",
    "Italian Cheese", "Gouda", "Havarti, Muenster & Brick",
    "Blue Cheese", "Soft Ripened & Brie",
    "Mixed Milk, Goat, Sheep & Feta",
    "Packaged Cheese", "Velveeta",
    // Cottage/cream cheese
    "Cottage Cheese", "Cream Cheese",
    // Butter
    "Butter & Margarine", "Salted Butter", "Unsalted butter",
    "Margarine & Butter Substitutes",
    // Yogurt
    "Yogurt", "Kefir",
    // Eggs
    "Eggs", "Egg Dishes",
    // Cream
    "Heavy Cream", "Sour Cream", "Half & Half",
    "Whipped Toppings",
    // Main umbrella
    "Dairy",
  ],
  seafood: [
    "Seafood", "Fish & Seafood", "Fresh Fish Fillets & Steaks",
    "Salmon", "Tuna", "Shellfish",
    "Oysters & Clams", "Sardines",
    "Canned Tuna & Seafood",
  ],
};

export async function GET(
  request: Request,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;
  const deptNames = DEPT_NAMES[slug.toLowerCase()] || [slug.replace(/-/g, " ")];
  
  const placeholders = deptNames.map(() => "?").join(",");
  
  const result = await turso.execute({
    sql: `
      SELECT p.name, p.price as iga_price, p.price_display as iga_display, p.size as iga_size, p.size_oz as iga_size_oz,
        pt_comp.name as tw_name, pt_comp.price as tw_price, pt_comp.price_display as tw_display, pt_comp.size as tw_size, pt_comp.size_oz as tw_size_oz,
        ROUND(pt_comp.price - p.price, 2) as gap,
        ROUND((pt_comp.price - p.price) / p.price * 100, 1) as gap_pct,
        ROUND(CASE WHEN p.size_oz IS NOT NULL AND pt_comp.size_oz IS NOT NULL
          THEN ABS(p.size_oz - pt_comp.size_oz) / CASE WHEN p.size_oz > pt_comp.size_oz THEN p.size_oz ELSE pt_comp.size_oz END
          ELSE NULL END, 2) as size_diff,
        pm.confidence, pm.match_quality,
        d.name as dept_name
      FROM products p
      JOIN product_matches pm ON p.id = pm.iga_product_id
      JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id
      JOIN departments d ON p.department_id = d.id
      WHERE p.store_id = 'iga-vashon'
        AND p.price IS NOT NULL AND pt_comp.price IS NOT NULL
        AND d.name IN (${placeholders})
      ORDER BY ABS(p.price - pt_comp.price) DESC
    `,
    args: deptNames,
  });

  return NextResponse.json(result.rows);
}
