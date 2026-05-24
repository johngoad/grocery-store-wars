import { NextResponse } from "next/server";
import turso from "@/db";
import { getCached, setCache, CACHE_5MIN } from "@/lib/cache";

const DEPT_NAMES: Record<string, string[]> = {
  produce: ["Apple","Apples","Avocados","Bananas & Plantains","Berries & Cherries","Blueberries","Cherries","Citrus","Fruit","Grape","Grapes","Melons","Mixed Fruit","Organic Fruits","Organic Fruits & Vegetables","Peaches","Pears","Pineapple","Stone Fruit","Strawberries","Tropical & Specialty","Beets","Broccoli","Broccoli & Cauliflower","Brussel Sprouts & Cabbage","Carrots","Carrots & Beets","Cauliflower","Celery","Corn","Cucumbers","Fresh Herbs","Green","Leafy Greens","Lettuce","Mushroom","Mushrooms","Okra","Onions","Onions & Garlic","Organic Vegetables","Peppers","Peppers & Chilis","Potato","Potatoes","Potatoes & Yams","Produce","Pumpkin","Radishes","Root Vegetables & Tropical Roots","Squash & Zucchini","Tomato","Tomatoes","Vegetable","Vegetable & Tomato","Vegetables","Veggie","Mixed Vegetables"],
  meat: ["Beef","Beef & Veal","Beef Roasts & Ribs","Ground Beef & Burgers","Burger, Ground Meat","Steaks & Fillets","Specialty Cuts","Kabobs, Stew, Cubes & Strips","Pork","Pork Roasts","Chops & Ribs","Ham","Loins","Chicken","Chicken Breasts","Chicken Legs, Thighs & Wings","Whole Chicken","Turkey","Ground Chicken","Ground Turkey & Burgers","Poultry","Wings","Lamb & Veal","Ground Meat","Ground Pork","Meat","Meat, Seafood & Poultry","Brat","Brats & Sausages","Sausage","Sausages","Kielbasa","Bacon"],
  dairy: ["1% Milk","2% Milk","Whole Milk","Milk","Milk & Cream","Skim & Nonfat","Lactose Free","Almond Milk","Coconut Milk","Soy Milk","Rice Milk","Milk Alternatives","Dry Milk","Powdered Milk","Evaporated Milk, Condensed Milk & Powdered Milk","Cheese","Cheddar","Colby","Monterey Jack","Mozzarella & Ricotta","Parmesan & Romano","Italian Cheese","Gouda","Havarti, Muenster & Brick","Blue Cheese","Soft Ripened & Brie","Mixed Milk, Goat, Sheep & Feta","Packaged Cheese","Velveeta","Cottage Cheese","Cream Cheese","Butter & Margarine","Salted Butter","Unsalted butter","Margarine & Butter Substitutes","Yogurt","Kefir","Eggs","Egg Dishes","Heavy Cream","Sour Cream","Half & Half","Whipped Toppings","Dairy"],
  seafood: ["Seafood","Fish & Seafood","Fresh Fish Fillets & Steaks","Salmon","Tuna","Shellfish","Oysters & Clams","Sardines","Canned Tuna & Seafood"],
};

export async function GET(request: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const key = `dept-${slug}`;
  const cached = getCached(key);
  if (cached) return NextResponse.json(cached, { headers: CACHE_5MIN });

  const deptNames = DEPT_NAMES[slug.toLowerCase()] || [slug.replace(/-/g, " ")];
  const placeholders = deptNames.map(() => "?").join(",");
  
  const result = await turso.execute({
    sql: `SELECT p.name, p.price as iga_price, p.price_display as iga_display, p.size as iga_size, p.size_oz as iga_size_oz, pt_comp.name as tw_name, pt_comp.price as tw_price, pt_comp.price_display as tw_display, pt_comp.size as tw_size, pt_comp.size_oz as tw_size_oz, ROUND(pt_comp.price - p.price, 2) as gap, ROUND((pt_comp.price - p.price) / p.price * 100, 1) as gap_pct, pm.match_quality, d.name as dept_name FROM products p JOIN product_matches pm ON p.id = pm.iga_product_id JOIN products pt_comp ON pm.thriftway_product_id = pt_comp.id JOIN departments d ON p.department_id = d.id WHERE p.store_id = 'iga-vashon' AND p.price IS NOT NULL AND pt_comp.price IS NOT NULL AND pm.match_quality != 'size_mismatch' AND d.name IN (${placeholders}) ORDER BY ABS(p.price - pt_comp.price) DESC LIMIT 200`,
    args: deptNames,
  });

  setCache(key, result.rows, 300);
  return NextResponse.json(result.rows, { headers: CACHE_5MIN });
}
