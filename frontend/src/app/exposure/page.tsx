"use client";

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Panel, Segmented } from "@/components/panel";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SCOPES, useScope } from "@/hooks/use-scope";
import { ASSET_CLASS, date, inr, inrCompact, pct } from "@/lib/format";
import { shortFundName } from "@/lib/holding";
import { useExposure } from "@/lib/queries";
import type { Exposure } from "@/lib/types";
import { cn } from "@/lib/utils";

function Figure({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="px-4 py-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="num mt-1 truncate text-lg font-medium">{value}</div>
      {sub && <div className="num truncate text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

function Bars({ rows, color }: { rows: { label: string; value: number; pct: number | null; color?: string }[]; color?: string }) {
  const max = Math.max(...rows.map((r) => r.pct ?? 0), 1);
  return (
    <ul className="num space-y-2.5">
      {rows.map((r) => (
        <li key={r.label}>
          <div className="flex items-baseline justify-between gap-3 text-[13px]">
            <span className="truncate">{r.label}</span>
            <span className="shrink-0 text-muted-foreground">
              {pct(r.pct, { digits: 1 })} <span className="text-[11px]">{inrCompact(r.value)}</span>
            </span>
          </div>
          <div className="mt-1 h-1.5 rounded-full bg-muted">
            <div className="h-full rounded-full" style={{ width: `${((r.pct ?? 0) / max) * 100}%`, background: r.color ?? color ?? "var(--foreground)" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function Companies({ data }: { data: Exposure }) {
  const [limit, setLimit] = useState(25);
  const [open, setOpen] = useState<string | null>(null);
  const rows = data.companies.slice(0, limit);
  const max = Math.max(...rows.map((c) => c.total), 1);

  return (
    <Panel
      title={<>Where your money really is <span className="font-normal text-muted-foreground">({data.companies_count} companies)</span></>}
      actions={
        <span className="flex items-center gap-3 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1"><span className="size-2 rounded-sm bg-foreground" />Direct</span>
          <span className="flex items-center gap-1"><span className="size-2 rounded-sm bg-accent-blue/60" />Through funds</span>
        </span>
      }
      bodyClassName="p-0"
    >
      <ul className="num divide-y divide-border/70 text-[13px]">
        {rows.map((c, i) => {
          const key = c.isin ?? c.name;
          const expanded = open === key;
          const href = c.symbol ? (c.tracked ? `/stock/?s=${encodeURIComponent(c.symbol)}` : `/stock/?isin=${c.isin}`) : null;
          return (
            <li key={key}>
              <div className="flex items-center gap-3 px-4 py-2">
                <span className="w-6 shrink-0 text-right text-[11px] text-text-tertiary">{i + 1}</span>
                <button type="button" onClick={() => setOpen(expanded ? null : key)} aria-expanded={expanded}
                  className="shrink-0 text-muted-foreground hover:text-foreground" aria-label={`Show where ${c.name} comes from`}>
                  {expanded ? <ChevronDownIcon className="size-4" /> : <ChevronRightIcon className="size-4" />}
                </button>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-3">
                    {href ? <Link href={href} className="truncate font-medium hover:text-accent-blue">{c.name}</Link> : <span className="truncate font-medium">{c.name}</span>}
                    <span className="shrink-0 whitespace-nowrap">
                      <span className="font-medium">{pct(c.weight_pct, { digits: 2 })}</span>
                      <span className="ml-2 text-muted-foreground">{inr(c.total)}</span>
                    </span>
                  </div>
                  <div className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-muted" style={{ width: `${(c.total / max) * 100}%` }}>
                    <div className="h-full bg-foreground" style={{ width: `${(c.direct / c.total) * 100}%` }} />
                    <div className="h-full bg-accent-blue/60" style={{ width: `${((c.total - c.direct) / c.total) * 100}%` }} />
                  </div>
                </div>
              </div>
              {expanded && (
                <ul className="space-y-1 bg-muted/50 py-2 pr-4 pl-[4.25rem] text-xs">
                  {c.direct > 0 && (
                    <li className="flex justify-between gap-3"><span>Held directly</span><span>{inr(c.direct)}</span></li>
                  )}
                  {c.via.map((v) => (
                    <li key={v.label} className="flex justify-between gap-3 text-muted-foreground">
                      <span className="truncate">Through {v.label}</span>
                      <span className="shrink-0">{inr(v.value)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
      {data.companies.length > limit && (
        <div className="border-t border-border p-2 text-center">
          <Button variant="ghost" size="sm" onClick={() => setLimit(100)}>Show top 100</Button>
        </div>
      )}
    </Panel>
  );
}

export default function ExposurePage() {
  const [scope, setScope] = useScope();
  const { data, isPending, isError, error } = useExposure(scope);

  let body: React.ReactNode;
  if (isPending) {
    body = <div className="space-y-4"><Skeleton className="h-20" /><Skeleton className="h-96" /></div>;
  } else if (isError) {
    body = <p className="py-16 text-loss">{error.message}</p>;
  } else if (data.total === 0) {
    body = <p className="py-16 text-muted-foreground">Nothing to look through yet. Add holdings first.</p>;
  } else {
    const top10 = data.companies.slice(0, 10).reduce((s, c) => s + (c.weight_pct ?? 0), 0);
    const largest = data.companies[0];
    const overlap = data.overlap[0];
    const sectorRows = data.sectors.slice(0, 20).map((s) => ({ label: s.sector, value: s.value, pct: s.weight_pct }));
    const rest = data.sectors.slice(20);
    if (rest.length) {
      sectorRows.push({ label: `${rest.length} other sectors`, value: rest.reduce((s, x) => s + x.value, 0), pct: rest.reduce((s, x) => s + (x.weight_pct ?? 0), 0) });
    }
    body = (
      <div className="space-y-4">
        <section aria-label="Concentration summary" className="rounded-md border border-border bg-surface">
          <div className="grid grid-cols-2 divide-x divide-border sm:grid-cols-3 lg:grid-cols-5 [&>*:nth-child(n+3)]:border-t sm:[&>*:nth-child(n+3)]:border-t-0 sm:[&>*:nth-child(n+4)]:border-t lg:[&>*:nth-child(n+4)]:border-t-0">
            <Figure label="Companies you own" value={data.companies_count} sub="directly or through funds" />
            <Figure label="Top 10 companies" value={pct(top10, { digits: 1 })} sub="of everything you hold" />
            <Figure label="Largest single company" value={largest ? pct(largest.weight_pct, { digits: 1 }) : "–"} sub={largest?.name} />
            <Figure label="Highest fund overlap" value={overlap ? pct(overlap.pct, { digits: 0 }) : "–"}
              sub={overlap ? `${shortFundName(overlap.a)} and ${shortFundName(overlap.b)}` : "no overlapping funds"} />
            <Figure label="Funds looked through" value={pct(data.coverage_pct, { digits: 0 })}
              sub={data.as_of.length ? `portfolios as of ${date(data.as_of[data.as_of.length - 1])}` : "no portfolios yet"} />
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <Companies data={data} />
          <div className="space-y-4">
            <Panel title="Sectors"><Bars rows={sectorRows} color="var(--accent-blue)" /></Panel>
            <Panel title="Asset mix">
              <Bars rows={data.assets.map((a) => ({ label: ASSET_CLASS[a.asset]?.label ?? a.asset, value: a.value, pct: a.weight_pct, color: ASSET_CLASS[a.asset]?.color }))} />
            </Panel>
          </div>
        </div>

        <Panel title="Fund overlap" actions={<span className="text-[11px] text-muted-foreground">Share of the same stocks, by weight</span>}>
          {data.overlap.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">Your funds don&apos;t hold the same stocks.</p>
          ) : (
            <ul className="num grid gap-x-8 gap-y-3 md:grid-cols-2">
              {data.overlap.slice(0, 12).map((o) => (
                <li key={`${o.a}|${o.b}`}>
                  <div className="flex items-baseline justify-between gap-3 text-[13px]">
                    <span className="truncate">{shortFundName(o.a)} <span className="text-muted-foreground">and</span> {shortFundName(o.b)}</span>
                    <span className={cn("shrink-0 font-medium", o.pct >= 40 && "text-loss")}>{pct(o.pct, { digits: 0 })}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-muted">
                    <div className={cn("h-full rounded-full", o.pct >= 40 ? "bg-loss/70" : "bg-foreground/60")} style={{ width: `${Math.min(100, o.pct)}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <p className="text-[11px] text-muted-foreground">
          Built from each fund&apos;s and ETF&apos;s latest published portfolio (fund houses publish monthly, about 10 days after month-end),
          weighted by what you hold today. Gold and silver ETFs count as gold and silver. Describes your holdings; it isn&apos;t a recommendation.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h1 className="text-lg font-medium">Exposure</h1>
        <Segmented label="Show" options={SCOPES} value={scope} onChange={setScope} />
      </div>
      {body}
    </>
  );
}
