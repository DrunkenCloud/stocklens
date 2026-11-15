"use client";

import { PlusIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useSyncExternalStore } from "react";

import { MfForm } from "@/components/mf/mf-form";
import { Segmented } from "@/components/panel";
import { Allocation } from "@/components/portfolio/allocation";
import { Figures } from "@/components/portfolio/figures";
import { Heatmap } from "@/components/portfolio/heatmap";
import { HoldingForm } from "@/components/portfolio/holding-form";
import { HoldingsTable } from "@/components/portfolio/holdings-table";
import { ValueChart } from "@/components/portfolio/value-chart";
import { loginToIcici } from "@/components/status-banner";
import { Button, buttonVariants } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { ago, date } from "@/lib/format";
import { holdingHref } from "@/lib/holding";
import { usePortfolio, useStatus } from "@/lib/queries";
import type { Holding, Scope } from "@/lib/types";
import { cn } from "@/lib/utils";

const SCOPES: { value: Scope; label: string }[] = [
  { value: "all", label: "Everything" },
  { value: "stocks", label: "Stocks & ETFs" },
  { value: "mf", label: "Mutual funds" },
];
const SCOPE_KEY = "stocklens.scope";

const scopeListeners = new Set<() => void>();
let scopeMemory: Scope = "all";

function readScope(): Scope {
  try {
    const saved = localStorage.getItem(SCOPE_KEY);
    if (SCOPES.some((s) => s.value === saved)) return saved as Scope;
  } catch {}
  return scopeMemory;
}

function subscribeScope(onChange: () => void) {
  scopeListeners.add(onChange);
  window.addEventListener("storage", onChange);
  return () => {
    scopeListeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

function useScope(): [Scope, (s: Scope) => void] {
  const scope = useSyncExternalStore(subscribeScope, readScope, () => "all" as Scope);
  const update = (next: Scope) => {
    scopeMemory = next;
    try {
      localStorage.setItem(SCOPE_KEY, next);
    } catch {}
    scopeListeners.forEach((l) => l());
  };
  return [scope, update];
}

export default function HoldingsPage() {
  const router = useRouter();
  const [scope, setScope] = useScope();
  const { data: portfolio, isPending, isError, error, refetch } = usePortfolio(scope);
  const { data: status } = useStatus();
  const [stockForm, setStockForm] = useState<{ open: boolean; holding: Holding | null }>({ open: false, holding: null });
  const [mfOpen, setMfOpen] = useState(false);

  const addMenu = (
    <DropdownMenu>
      <DropdownMenuTrigger className={cn(buttonVariants({ size: "sm", variant: "outline" }))}>
        <PlusIcon /> Add
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setStockForm({ open: true, holding: null })}>Stock or ETF</DropdownMenuItem>
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
          ICICI stocks come in on their own after you log in to ICICI. Add what you hold elsewhere: stocks with shares and
          total invested, mutual funds with what you bought and sold.
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
          <div className="lg:col-span-2"><ValueChart pricedInvested={portfolio.totals.priced_invested} scope={scope} /></div>
          <Allocation portfolio={portfolio} />
        </div>
        <Heatmap holdings={portfolio.holdings} />
        <HoldingsTable
          holdings={portfolio.holdings}
          addAction={addMenu}
          onEdit={(h) => (h.kind === "mf" ? router.push(holdingHref(h)) : setStockForm({ open: true, holding: h }))}
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
      <HoldingForm open={stockForm.open} holding={stockForm.holding} onOpenChange={(open) => setStockForm((f) => ({ ...f, open }))} />
      <MfForm open={mfOpen} onOpenChange={setMfOpen} target={{}} />
    </>
  );
}
