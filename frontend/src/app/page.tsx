import { StatsCards } from "@/components/dashboard/stats-cards";
import { PositionMap } from "@/components/dashboard/position-map";
import { QuickWins } from "@/components/dashboard/quick-wins";
import { DepartmentNav } from "@/components/dashboard/department-nav";
import { MarginTable } from "@/components/dashboard/margin-table";
import { BigGapsTable } from "@/components/dashboard/big-gaps-table";
import { StaplesTable } from "@/components/dashboard/staples-table";
import { NeedsReviewTable } from "@/components/dashboard/needs-review-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Store, AlertTriangle, TrendingUp, ShoppingBasket, ZoomIn, BarChart3 } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Store className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground tracking-tight">GSW</h1>
                <p className="text-xs text-muted-foreground font-medium">IGA Vashon Competitive Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-muted-foreground bg-muted px-3 py-1.5 rounded-full border border-border">
                vs Thriftway
              </span>
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-200 dark:border-emerald-500/20">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <section>
          <StatsCards />
        </section>

        <section>
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-4 w-4 text-emerald-500" />
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Strategy View</h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3">
              <PositionMap />
            </div>
            <div className="lg:col-span-2">
              <QuickWins />
            </div>
          </div>
        </section>

        <section>
          <div className="flex items-center gap-2 mb-3">
            <Store className="h-4 w-4 text-emerald-500" />
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Departments</h2>
          </div>
          <DepartmentNav />
        </section>

        <section>
          <Tabs defaultValue="gaps" className="w-full">
            <TabsList className="w-full justify-start gap-1 bg-muted p-1 rounded-xl border border-border">
              <TabsTrigger value="gaps" className="flex items-center gap-2 data-[state=active]:bg-emerald-100 data-[state=active]:text-emerald-700 dark:data-[state=active]:bg-emerald-500/15 dark:data-[state=active]:text-emerald-400 data-[state=active]:shadow-sm rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all">
                <AlertTriangle className="h-3.5 w-3.5" /> Big Gaps
              </TabsTrigger>
              <TabsTrigger value="margins" className="flex items-center gap-2 data-[state=active]:bg-amber-100 data-[state=active]:text-amber-700 dark:data-[state=active]:bg-amber-500/15 dark:data-[state=active]:text-amber-400 data-[state=active]:shadow-sm rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all">
                <TrendingUp className="h-3.5 w-3.5" /> Margin Ops
              </TabsTrigger>
              <TabsTrigger value="review" className="flex items-center gap-2 data-[state=active]:bg-blue-100 data-[state=active]:text-blue-700 dark:data-[state=active]:bg-blue-500/15 dark:data-[state=active]:text-blue-400 data-[state=active]:shadow-sm rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all">
                <ZoomIn className="h-3.5 w-3.5" /> Review
              </TabsTrigger>
              <TabsTrigger value="staples" className="flex items-center gap-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700 dark:data-[state=active]:bg-purple-500/15 dark:data-[state=active]:text-purple-400 data-[state=active]:shadow-sm rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all">
                <ShoppingBasket className="h-3.5 w-3.5" /> Staples
              </TabsTrigger>
            </TabsList>
            <TabsContent value="gaps" className="mt-6">
              <BigGapsTable />
            </TabsContent>
            <TabsContent value="margins" className="mt-6">
              <MarginTable />
            </TabsContent>
            <TabsContent value="review" className="mt-6">
              <NeedsReviewTable />
            </TabsContent>
            <TabsContent value="staples" className="mt-6">
              <StaplesTable />
            </TabsContent>
          </Tabs>
        </section>

        <footer className="pt-8 pb-4 text-center">
          <p className="text-xs text-muted-foreground">
            GSW · IGA Vashon · Vashon Island, WA · Live price data
          </p>
        </footer>
      </main>
    </div>
  );
}
