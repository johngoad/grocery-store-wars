import Link from "next/link";
import { Apple, Beef, Milk, Fish } from "lucide-react";

// Mirror the department name mappings from api/departments/[slug]/route.ts
const DEPARTMENTS = [
  { slug: "produce", label: "Produce", icon: Apple },
  { slug: "meat", label: "Meat", icon: Beef },
  { slug: "dairy", label: "Dairy & Eggs", icon: Milk },
  { slug: "seafood", label: "Seafood", icon: Fish },
];

export function DepartmentNav() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {DEPARTMENTS.map((dept) => {
        const Icon = dept.icon;
        return (
          <Link
            key={dept.slug}
            href={`/departments/${dept.slug}`}
            className="flex items-center gap-3 p-4 rounded-xl bg-card border border-border hover:border-emerald-300 dark:hover:border-emerald-500/30 hover:shadow-sm transition-all group"
          >
            <div className="h-10 w-10 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-100 dark:group-hover:bg-emerald-500/20 transition-colors shrink-0">
              <Icon className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">{dept.label}</p>
              <p className="text-xs text-muted-foreground">View breakdown</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
