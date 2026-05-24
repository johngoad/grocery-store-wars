"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useData } from "@/hooks/useData";
import { TrendingUp, TrendingDown, Target, ArrowRight } from "lucide-react";

export function QuickWins() {
  const raise = useData("/api/margins?limit=6&direction=raise");
  const undercut = useData("/api/margins?limit=6&direction=undercut");
  const isLoading = raise.isLoading || undercut.isLoading;

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Quick Wins</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-[420px] w-full" /></CardContent>
      </Card>
    );
  }

  const raiseItems = (raise.data || []).slice(0, 6);
  const cutItems = (undercut.data || []).slice(0, 6);

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-amber-500" />
          <CardTitle className="text-base font-semibold">Quick Wins</CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          Highest-impact price moves. Sizes verified, weight-matched.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Raise section */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="h-7 w-7 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h3 className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              Raise These
            </h3>
            <span className="text-xs text-muted-foreground">— you&apos;re cheaper than Thriftway</span>
          </div>
          <div className="space-y-2">
            {raiseItems.map((item: any, i: number) => {
              const gap = Number(item.gap);
              return (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-emerald-50/40 dark:bg-emerald-500/5 border border-emerald-200/50 dark:border-emerald-500/10 hover:border-emerald-300 dark:hover:border-emerald-500/30 transition-colors group">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs font-mono-data text-emerald-600 dark:text-emerald-400 font-semibold">
                        IGA {item.iga_display}
                      </span>
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs font-mono-data text-muted-foreground">
                        TW {item.tw_display}
                      </span>
                    </div>
                  </div>
                  <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-mono-data text-xs whitespace-nowrap">
                    +${gap.toFixed(2)}
                  </Badge>
                </div>
              );
            })}
          </div>
        </div>

        {/* Cut section */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="h-7 w-7 rounded-lg bg-red-50 dark:bg-red-500/10 flex items-center justify-center">
              <TrendingDown className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
            </div>
            <h3 className="text-sm font-semibold text-red-700 dark:text-red-400">
              Cut These
            </h3>
            <span className="text-xs text-muted-foreground">— you&apos;re pricier than Thriftway</span>
          </div>
          <div className="space-y-2">
            {cutItems.map((item: any, i: number) => {
              const gap = Math.abs(Number(item.gap));
              return (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-red-50/40 dark:bg-red-500/5 border border-red-200/50 dark:border-red-500/10 hover:border-red-300 dark:hover:border-red-500/30 transition-colors group">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs font-mono-data text-red-600 dark:text-red-400 font-semibold">
                        IGA {item.iga_display}
                      </span>
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs font-mono-data text-muted-foreground">
                        TW {item.tw_display}
                      </span>
                    </div>
                  </div>
                  <Badge className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 font-mono-data text-xs whitespace-nowrap">
                    -${gap.toFixed(2)}
                  </Badge>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
