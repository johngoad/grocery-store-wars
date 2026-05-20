import { StatsCards } from "@/components/dashboard/stats-cards";
import { DepartmentChart } from "@/components/dashboard/department-chart";
import { PricePositionChart } from "@/components/dashboard/price-position-chart";
import { MarginTable } from "@/components/dashboard/margin-table";
import { BigGapsTable } from "@/components/dashboard/big-gaps-table";
import { StaplesTable } from "@/components/dashboard/staples-table";
import { NeedsReviewTable } from "@/components/dashboard/needs-review-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Store, AlertTriangle, TrendingUp, ShoppingBasket, ZoomIn } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-emerald-600 flex items-center justify-center">
              <Store className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-zinc-900 dark:text-white leading-tight">GSW</h1>
              <p className="text-xs text-zinc-500">IGA Vashon Competitive Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-2.5 py-1 rounded-full">
              vs Thriftway
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        <StatsCards />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DepartmentChart />
          <PricePositionChart />
        </div>

        <Tabs defaultValue="gaps" className="w-full">
          <TabsList className="w-full justify-start gap-1 bg-zinc-100 dark:bg-zinc-900 p-1 rounded-lg">
            <TabsTrigger value="gaps" className="flex items-center gap-1.5 data-[state=active]:bg-white dark:data-[state=active]:bg-zinc-800">
              <AlertTriangle className="h-3.5 w-3.5" /> Big Gaps
            </TabsTrigger>
            <TabsTrigger value="margins" className="flex items-center gap-1.5 data-[state=active]:bg-white dark:data-[state=active]:bg-zinc-800">
              <TrendingUp className="h-3.5 w-3.5" /> Margin Ops
            </TabsTrigger>
            <TabsTrigger value="review" className="flex items-center gap-1.5 data-[state=active]:bg-white dark:data-[state=active]:bg-zinc-800">
              <ZoomIn className="h-3.5 w-3.5" /> Review
            </TabsTrigger>
            <TabsTrigger value="staples" className="flex items-center gap-1.5 data-[state=active]:bg-white dark:data-[state=active]:bg-zinc-800">
              <ShoppingBasket className="h-3.5 w-3.5" /> Staples
            </TabsTrigger>
          </TabsList>
          <TabsContent value="gaps" className="mt-4">
            <BigGapsTable />
          </TabsContent>
          <TabsContent value="margins" className="mt-4">
            <MarginTable />
          </TabsContent>
          <TabsContent value="review" className="mt-4">
            <NeedsReviewTable />
          </TabsContent>
          <TabsContent value="staples" className="mt-4">
            <StaplesTable />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
