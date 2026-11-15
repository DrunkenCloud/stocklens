"use client";

import { LoaderCircleIcon } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { openIciciLogin, useStatus } from "@/lib/queries";

const JOB_LABELS: Record<string, string> = {
  sync_icici: "Updating prices after your ICICI login",
  fetch_prices: "Updating prices",
  fetch_fundamentals: "Updating company fundamentals",
  refresh_securities: "Refreshing the list of listed stocks",
  onboard: "Loading data for a newly tracked stock",
  refresh_mf: "Updating fund NAVs",
  refresh_fund_portfolios: "Loading fund portfolios",
};

export async function loginToIcici() {
  try {
    await openIciciLogin();
  } catch (e) {
    toast.error((e as Error).message);
  }
}

export function StatusBanner() {
  const { data: status, isError } = useStatus();

  if (isError) {
    return <Strip tone="warn">Can&apos;t reach the StockLens server. Numbers below may be out of date.</Strip>;
  }
  if (!status) return null;

  if (status.running.length) {
    const job = status.running.includes("sync_icici") ? "sync_icici" : status.running[0];
    return (
      <Strip tone="info">
        <LoaderCircleIcon className="size-4 animate-spin" aria-hidden />
        {JOB_LABELS[job] ?? "Updating data"}…
      </Strip>
    );
  }
  if (status.breeze.state !== "valid") {
    return (
      <Strip tone="warn">
        <span className="flex-1">
          {status.breeze.state === "never" ? "ICICI isn't connected yet." : "Today's ICICI login has expired or hasn't happened yet."}{" "}
          Log in to ICICI to update today&apos;s prices.
        </span>
        <Button size="sm" onClick={loginToIcici}>Log in to ICICI</Button>
      </Strip>
    );
  }
  if (status.last_sync?.status === "failed") {
    return (
      <Strip tone="warn">
        <span className="flex-1">
          {status.last_sync.summary?.startsWith("updated after login")
            ? `Prices updated after your ICICI login, but not everything (${status.last_sync.summary.split("; ").slice(1).join(", ")}).`
            : `The last update after ICICI login failed: ${status.last_sync.summary ?? "no details"}`}
        </span>
        <Link href="/admin" className="font-medium underline underline-offset-4">See details</Link>
      </Strip>
    );
  }
  return null;
}

function Strip({ tone, children }: { tone: "info" | "warn"; children: React.ReactNode }) {
  return (
    <div
      role="status"
      className={
        tone === "warn"
          ? "border-b border-broker-icici/40 bg-broker-icici/10 text-foreground"
          : "border-b border-border bg-secondary text-secondary-foreground"
      }
    >
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-3 gap-y-2 px-4 py-2 text-sm">{children}</div>
    </div>
  );
}
