"use client";

import { PlusIcon } from "lucide-react";
import { useState } from "react";

import { HoldingForm } from "@/components/portfolio/holding-form";
import { HoldingsTable } from "@/components/portfolio/holdings-table";
import { Sectors } from "@/components/portfolio/sectors";
import { Summary } from "@/components/portfolio/summary";
import { loginToIcici } from "@/components/status-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
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
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-14 w-72" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="mt-8 h-64 w-full" />
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
        <h1 className="text-3xl font-semibold tracking-tight">Nothing here yet</h1>
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
    body = (
      <div className="space-y-10">
        <Summary portfolio={portfolio} status={status} />
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_16rem]">
          <section aria-labelledby="holdings-heading">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 id="holdings-heading" className="text-base font-semibold">
                Holdings <span className="font-normal text-muted-foreground">{portfolio.holdings.length}</span>
              </h2>
              <Button size="sm" variant="outline" onClick={openNew}><PlusIcon /> Add holding</Button>
            </div>
            <HoldingsTable holdings={portfolio.holdings} onEdit={(holding) => setForm({ open: true, holding })} />
          </section>
          <aside><Sectors sectors={portfolio.by_sector} /></aside>
        </div>
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
