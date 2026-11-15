"use client";

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Panel } from "@/components/panel";
import { loginToIcici } from "@/components/status-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ago, date, time } from "@/lib/format";
import { useCompanies, useRun, useRuns, useStatus, useTriggerJob } from "@/lib/queries";
import type { JobRun, JobStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const JOBS: Record<string, { label: string; detail: string }> = {
  sync_icici: { label: "Update after login", detail: "Fetch prices and any missing fundamentals. Needs today's ICICI login." },
  fetch_prices: { label: "Update prices", detail: "Fetch new daily prices for every tracked stock." },
  fetch_fundamentals: { label: "Update fundamentals", detail: "Refresh ratios from Yahoo Finance for every tracked stock." },
  refresh_securities: { label: "Refresh stock list", detail: "Re-download ICICI's list of NSE and BSE stocks used by search." },
  fetch_prices_backfill: { label: "Reload price history", detail: "Re-download full daily history since 2015. Takes a while." },
  onboard: { label: "Load new stock", detail: "" },
  refresh_mf: { label: "Update fund NAVs", detail: "Load every mutual fund's latest NAV from AMFI and fill in history for your funds." },
};

const STATUS_STYLE: Record<JobStatus, string> = {
  running: "bg-accent-blue/15 text-accent-blue",
  done: "bg-gain-soft text-gain",
  failed: "bg-loss-soft text-loss",
  skipped: "bg-muted text-muted-foreground",
};

const SESSION_TEXT = {
  valid: "Connected for today. Prices update automatically.",
  expired: "Today's session has expired or hasn't started. Log in to update prices.",
  never: "Not connected yet. Log in once a day so prices can update.",
};

function duration(run: JobRun) {
  if (!run.finished_at) return "";
  const s = Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

export default function DataPage() {
  const { data: status } = useStatus();
  const runs = useRuns();
  const companies = useCompanies();
  const trigger = useTriggerJob();
  const [open, setOpen] = useState<number | null>(null);

  const start = (name: string) =>
    trigger.mutate(name, {
      onSuccess: () => toast.success(`${JOBS[name]?.label ?? name} started`),
      onError: (e) => toast.error(e.message),
    });

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-medium">Data</h1>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="ICICI connection">
          <div className="flex items-center gap-2">
            <span className={cn("size-2 rounded-full", status?.breeze.state === "valid" ? "bg-gain" : "bg-broker-icici")} aria-hidden />
            <span className="font-medium">{status?.breeze.state === "valid" ? "Connected" : "Not connected"}</span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{status ? SESSION_TEXT[status.breeze.state] : " "}</p>
          {status?.breeze.captured_at && <p className="mt-1 text-xs text-muted-foreground">Last login {time(status.breeze.captured_at)}</p>}
          <Button className="mt-4" variant={status?.breeze.state === "valid" ? "outline" : "default"} onClick={loginToIcici}>
            {status?.breeze.state === "valid" ? "Log in again" : "Log in to ICICI"}
          </Button>
        </Panel>

        <Panel title="Run a job" className="lg:col-span-2">
          <ul className="divide-y divide-border">
            {(runs.data?.jobs ?? []).map((name) => {
              const running = status?.running.includes(name.replace("_backfill", ""));
              return (
                <li key={name} className="flex items-center justify-between gap-4 py-2.5 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <div className="text-[13px] font-medium">{JOBS[name]?.label ?? name}</div>
                    <div className="text-xs text-muted-foreground">{JOBS[name]?.detail}</div>
                  </div>
                  <Button size="sm" variant="outline" disabled={running || trigger.isPending} onClick={() => start(name)}>
                    {running ? "Running…" : "Run"}
                  </Button>
                </li>
              );
            })}
          </ul>
        </Panel>
      </div>

      <Panel title="Recent runs" bodyClassName="p-0">
        {runs.isPending ? (
          <Skeleton className="m-4 h-40" />
        ) : !runs.data?.runs.length ? (
          <p className="p-8 text-center text-sm text-muted-foreground">No jobs have run yet.</p>
        ) : (
          <ul className="divide-y divide-border/70 text-[13px]">
            {runs.data.runs.map((r) => (
              <li key={r.id}>
                <button type="button" onClick={() => setOpen(open === r.id ? null : r.id)} aria-expanded={open === r.id}
                  className="grid w-full grid-cols-[1rem_1fr_auto] items-start gap-x-3 gap-y-1 px-4 py-2.5 text-left hover:bg-muted/60 md:grid-cols-[1rem_11rem_5rem_1fr_7rem]">
                  {open === r.id ? <ChevronDownIcon className="mt-0.5 size-4 text-muted-foreground" /> : <ChevronRightIcon className="mt-0.5 size-4 text-muted-foreground" />}
                  <span className="font-medium">
                    {JOBS[r.job === "fetch_prices" && r.args.includes("--backfill") ? "fetch_prices_backfill" : r.job]?.label ?? r.job}
                    <span className="block text-[11px] font-normal text-muted-foreground">
                      {r.trigger === "cron" ? "Scheduled" : r.trigger === "auto" ? "Automatic" : "Manual"}{r.args && !r.args.includes("--backfill") ? `, ${r.args.replace("--symbols ", "")}` : ""}
                    </span>
                  </span>
                  <span className={cn("w-fit rounded px-1.5 py-0.5 text-[11px] capitalize md:order-none", STATUS_STYLE[r.status])}>{r.status}</span>
                  <span className="col-span-2 col-start-2 truncate text-muted-foreground md:col-span-1 md:col-start-auto">{r.summary}</span>
                  <span className="num col-span-2 col-start-2 text-[11px] text-muted-foreground md:col-span-1 md:col-start-auto md:text-right">
                    {ago(r.started_at)}{duration(r) && `, ${duration(r)}`}
                  </span>
                </button>
                {open === r.id && <RunLog id={r.id} />}
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel title={<>Tracked stocks <span className="font-normal text-muted-foreground">({companies.data?.length ?? 0})</span></>} bodyClassName="p-0">
        {companies.isPending ? (
          <Skeleton className="m-4 h-32" />
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <table className="num w-full text-[13px]">
              <thead className="sticky top-0 bg-surface">
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="py-2 pl-4 font-normal">Stock</th>
                  <th className="hidden px-3 py-2 font-normal sm:table-cell">Sector</th>
                  <th className="px-3 py-2 text-right font-normal">Latest price</th>
                </tr>
              </thead>
              <tbody>
                {companies.data?.map((c) => (
                  <tr key={c.symbol} className="border-b border-border/70 last:border-0">
                    <td className="py-1.5 pl-4"><span className="font-medium">{c.symbol}</span> <span className="text-muted-foreground">{c.name}</span></td>
                    <td className="hidden px-3 py-1.5 text-muted-foreground sm:table-cell">{c.sector ?? "–"}</td>
                    <td className="px-3 py-1.5 text-right text-muted-foreground">{c.price_date ? date(c.price_date) : "No prices yet"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

function RunLog({ id }: { id: number }) {
  const { data, isPending } = useRun(id);
  return (
    <pre className="max-h-80 overflow-auto border-t border-border bg-muted px-4 py-3 font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-muted-foreground">
      {isPending ? "Loading log…" : data?.log_tail || "No output."}
    </pre>
  );
}
