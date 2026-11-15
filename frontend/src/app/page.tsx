"use client";

import { PlusIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { MfForm } from "@/components/mf/mf-form";
import { Segmented } from "@/components/panel";
import { Allocation } from "@/components/portfolio/allocation";
import { Figures } from "@/components/portfolio/figures";
import { Heatmap } from "@/components/portfolio/heatmap";
import { HoldingsTable } from "@/components/portfolio/holdings-table";
import { GrowthChart } from "@/components/portfolio/growth-chart";
import { StockEntryForm } from "@/components/portfolio/stock-entry-form";
import { loginToIcici } from "@/components/status-banner";
import { Button, buttonVariants } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { ago, date } from "@/lib/format";
import { holdingHref } from "@/lib/holding";
import { usePortfolio, useStatus } from "@/lib/queries";
import { cn } from "@/lib/utils";
import { SCOPES, useScope } from "@/hooks/use-scope";

export default function HoldingsPage() {
  const router = useRouter();
  const [scope, setScope] = useScope();
  const { data: portfolio, isPending, isError, error, refetch } = usePortfolio(scope);
  const { data: status } = useStatus();
  const [stockOpen, setStockOpen] = useState(false);
  const [mfOpen, setMfOpen] = useState(false);

  const addMenu = (
    <DropdownMenu>
      <DropdownMenuTrigger className={cn(buttonVariants({ size: "sm", variant: "outline" }))}>
        <PlusIcon /> Add
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setStockOpen(true)}>Stock or ETF</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setMfOpen(true)}>Mutual fund</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  let body: React.ReactNode;
  if (isPending) {
    body = (
      <div className="space-y-4" aria-busy>
        <Skeleton className="h-20 w-full" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-80 lg:col-span-2" />
          <Skeleton className="h-80" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  } else if (isError) {
    body = (
      <div className="py-16">
        <p className="text-loss">{error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => refetch()}>Try again</Button>
      </div>
    );
  } else if (portfolio.holdings.length === 0) {
    body = (
      <div className="max-w-lg py-12">
        <h2 className="text-2xl font-medium tracking-tight">{scope === "mf" ? "No mutual funds yet" : "No holdings yet"}</h2>
        <p className="mt-3 text-muted-foreground">
          Add what you bought and sold at any broker, with dates, and StockLens works out holdings, returns and XIRR.
          Log in to ICICI daily so prices stay current.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          {status?.breeze.state !== "valid" && <Button onClick={loginToIcici}>Log in to ICICI</Button>}
          {addMenu}
        </div>
      </div>
    );
  } else {
    const unpriced = portfolio.holdings.filter((h) => h.value === null).length;
    body = (
      <div className="space-y-4">
        <Figures portfolio={portfolio} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2"><GrowthChart scope={scope} /></div>
          <Allocation portfolio={portfolio} />
        </div>
        <Heatmap holdings={portfolio.holdings} />
        <HoldingsTable
          holdings={portfolio.holdings}
          addAction={addMenu}
          onEdit={(h) => router.push(holdingHref(h))}
        />
        {unpriced > 0 && <p className="text-xs text-muted-foreground">{unpriced} holding{unpriced > 1 ? "s" : ""} awaiting a first price, left out of value and returns.</p>}
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h1 className="text-lg font-medium">Holdings</h1>
          <p className="text-xs text-muted-foreground">
            Prices as of {date(status?.prices_as_of)}
            {status?.last_sync?.status === "done" && `, ICICI synced ${ago(status.last_sync.finished_at)}`}
          </p>
        </div>
        <Segmented label="Show" options={SCOPES} value={scope} onChange={setScope} />
      </div>
      {body}
      <StockEntryForm open={stockOpen} onOpenChange={setStockOpen} target={{}} />
      <MfForm open={mfOpen} onOpenChange={setMfOpen} target={{}} />
    </>
  );
}
