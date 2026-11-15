"use client";

import { PlusIcon } from "lucide-react";
import { useState } from "react";

import { Allocation } from "@/components/portfolio/allocation";
import { Figures } from "@/components/portfolio/figures";
import { Heatmap } from "@/components/portfolio/heatmap";
import { HoldingForm } from "@/components/portfolio/holding-form";
import { HoldingsTable } from "@/components/portfolio/holdings-table";
import { ValueChart } from "@/components/portfolio/value-chart";
import { loginToIcici } from "@/components/status-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ago, date } from "@/lib/format";
import { usePortfolio, useStatus } from "@/lib/queries";
import type { Holding } from "@/lib/types";

export default function HoldingsPage() {
  const { data: portfolio, isPending, isError, error, refetch } = usePortfolio();
  const { data: status } = useStatus();
  const [form, setForm] = useState<{ open: boolean; holding: Holding | null }>({ open: false, holding: null });
  const openNew = () => setForm({ open: true, holding: null });

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
        <h1 className="text-2xl font-medium tracking-tight">No holdings yet</h1>
        <p className="mt-3 text-muted-foreground">
          Log in to ICICI and your ICICI holdings come in on their own. For Zerodha, Groww or anywhere else,
          add each stock with how many shares you hold and what you paid in total.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          {status?.breeze.state !== "valid" && <Button onClick={loginToIcici}>Log in to ICICI</Button>}
          <Button variant="outline" onClick={openNew}><PlusIcon /> Add a holding</Button>
        </div>
      </div>
    );
  } else {
    const unpriced = portfolio.holdings.filter((h) => h.value === null).length;
    body = (
      <div className="space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h1 className="text-lg font-medium">Holdings</h1>
          <p className="text-xs text-muted-foreground">
            Prices as of {date(status?.prices_as_of)}
            {status?.last_sync?.status === "done" && `, ICICI synced ${ago(status.last_sync.finished_at)}`}
            {unpriced > 0 && `. ${unpriced} awaiting a first price, left out of value and returns.`}
          </p>
        </div>
        <Figures portfolio={portfolio} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2"><ValueChart pricedInvested={portfolio.totals.priced_invested} /></div>
          <Allocation portfolio={portfolio} />
        </div>
        <Heatmap holdings={portfolio.holdings} />
        <HoldingsTable holdings={portfolio.holdings} onAdd={openNew} onEdit={(holding) => setForm({ open: true, holding })} />
      </div>
    );
  }

  return (
    <>
      {body}
      <HoldingForm open={form.open} holding={form.holding} onOpenChange={(open) => setForm((f) => ({ ...f, open }))} />
    </>
  );
}
