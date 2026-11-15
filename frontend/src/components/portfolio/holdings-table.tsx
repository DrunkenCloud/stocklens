"use client";

import { ArrowDownIcon, ArrowUpIcon, PencilIcon } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Sparkline } from "@/components/charts/sparkline";
import { Panel } from "@/components/panel";
import type { Holding } from "@/lib/types";
import { brokerColor, inr, num, pct, qty, tone } from "@/lib/format";
import { holdingHref, holdingTitle } from "@/lib/holding";
import { cn } from "@/lib/utils";

type SortKey = "name" | "quantity" | "avg_cost" | "close" | "invested" | "value" | "pnl" | "pnl_pct" | "day_change_pct";

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "name", label: "Instrument" },
  { key: "quantity", label: "Qty", align: "right" },
  { key: "avg_cost", label: "Avg cost", align: "right" },
  { key: "close", label: "LTP", align: "right" },
  { key: "invested", label: "Invested", align: "right" },
  { key: "value", label: "Cur. value", align: "right" },
  { key: "pnl", label: "P&L", align: "right" },
  { key: "pnl_pct", label: "Net chg", align: "right" },
  { key: "day_change_pct", label: "Day chg", align: "right" },
];


function sortValue(h: Holding, key: SortKey): number | string {
  if (key === "name") return h.symbol;
  return h[key] ?? Number.NEGATIVE_INFINITY;
}

const units = (h: Holding) => (h.kind === "mf" ? num(h.quantity, 3) : qty(h.quantity));

export function HoldingsTable({ holdings, onEdit, addAction }: { holdings: Holding[]; onEdit: (h: Holding) => void; addAction: React.ReactNode }) {
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "value", dir: -1 });
  const [broker, setBroker] = useState<string | null>(null);

  const brokers = useMemo(() => [...new Set(holdings.map((h) => h.broker))], [holdings]);
  const rows = useMemo(() => {
    const filtered = broker ? holdings.filter((h) => h.broker === broker) : holdings;
    return [...filtered].sort((a, b) => {
      const x = sortValue(a, sort.key), y = sortValue(b, sort.key);
      return (x < y ? -1 : x > y ? 1 : 0) * sort.dir;
    });
  }, [holdings, broker, sort]);

  const totals = useMemo(() => {
    const priced = rows.filter((h) => h.value !== null);
    const invested = rows.reduce((s, h) => s + h.invested, 0);
    const pricedInvested = priced.reduce((s, h) => s + h.invested, 0);
    const value = priced.reduce((s, h) => s + (h.value ?? 0), 0);
    const pnl = value - pricedInvested;
    return { invested, value, pnl, pnlPct: pricedInvested ? (pnl / pricedInvested) * 100 : null };
  }, [rows]);

  const toggleSort = (key: SortKey) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 1 ? -1 : 1 } : { key, dir: key === "name" ? 1 : -1 }));

  return (
    <Panel
      title={<>Holdings <span className="font-normal text-muted-foreground">({holdings.length})</span></>}
      actions={
        <>
          {brokers.length > 1 && (
            <select
              aria-label="Filter by broker"
              value={broker ?? ""}
              onChange={(e) => setBroker(e.target.value || null)}
              className="h-7 rounded border border-border bg-surface px-2 text-xs"
            >
              <option value="">All brokers</option>
              {brokers.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          )}
          {addAction}
        </>
      }
      bodyClassName="p-0"
    >
      <div className="hidden overflow-x-auto lg:block">
        <table className="num w-full text-[13px]">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              {COLUMNS.map((c) => (
                <th
                  key={c.key}
                  scope="col"
                  aria-sort={sort.key === c.key ? (sort.dir === 1 ? "ascending" : "descending") : undefined}
                  className={cn("px-3 py-2 font-normal first:pl-4", c.align === "right" ? "text-right" : "text-left")}
                >
                  <button type="button" onClick={() => toggleSort(c.key)} className="inline-flex items-center gap-1 hover:text-foreground">
                    {c.label}
                    {sort.key === c.key && (sort.dir === 1 ? <ArrowUpIcon className="size-3" /> : <ArrowDownIcon className="size-3" />)}
                  </button>
                </th>
              ))}
              <th scope="col" className="px-3 py-2 text-right font-normal">30D</th>
              <th className="w-10 pr-2"><span className="sr-only">Edit</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              <tr key={h.id} className="group border-b border-border/70 hover:bg-muted/60">
                <td className="py-2 pr-3 pl-4">
                  <Link href={holdingHref(h)} className="flex items-center gap-2">
                    <span className="h-6 w-0.5 shrink-0 rounded-full" style={{ background: brokerColor(h.broker) }} title={h.broker} />
                    <span className="min-w-0">
                      <span className="flex max-w-72 items-center gap-1.5 font-medium group-hover:text-accent-blue">
                        <span className="truncate">{holdingTitle(h)}</span>
                        {h.kind === "mf" && <span className="rounded bg-muted px-1 text-[10px] font-normal text-muted-foreground">MF</span>}
                        {h.kind === "etf" && <span className="rounded bg-muted px-1 text-[10px] font-normal text-muted-foreground">ETF</span>}
                        {h.exchange === "BSE" && <span className="rounded bg-muted px-1 text-[10px] font-normal text-muted-foreground">BSE</span>}
                      </span>
                      <span className="block max-w-56 truncate text-[11px] text-muted-foreground">
                        {h.broker}{h.source === "icici_sync" ? " (synced)" : ""}
                      </span>
                    </span>
                  </Link>
                </td>
                <td className="px-3 py-2 text-right">{units(h)}</td>
                <td className="px-3 py-2 text-right">{inr(h.avg_cost, { precise: true })}</td>
                <td className="px-3 py-2 text-right">{h.close === null ? <span className="text-text-tertiary">Awaiting</span> : inr(h.close, { precise: true })}</td>
                <td className="px-3 py-2 text-right">{inr(h.invested, { precise: true })}</td>
                <td className="px-3 py-2 text-right">{inr(h.value, { precise: true })}</td>
                <td className={cn("px-3 py-2 text-right", tone(h.pnl))}>{inr(h.pnl, { precise: true, signed: true })}</td>
                <td className={cn("px-3 py-2 text-right", tone(h.pnl_pct))}>{pct(h.pnl_pct, { signed: true })}</td>
                <td className={cn("px-3 py-2 text-right", tone(h.day_change_pct))}>{pct(h.day_change_pct, { signed: true })}</td>
                <td className="px-3 py-1 text-right"><Sparkline values={h.spark} /></td>
                <td className="pr-2 text-right">
                  {h.source === "manual" && (
                    <button type="button" onClick={() => onEdit(h)} aria-label={`Edit ${holdingTitle(h)} at ${h.broker}`}
                      className="rounded p-1.5 text-text-tertiary opacity-0 group-hover:opacity-100 hover:bg-muted hover:text-foreground focus-visible:opacity-100">
                      <PencilIcon className="size-3.5" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="font-medium">
              <td className="py-2.5 pl-4" colSpan={4}>Total</td>
              <td className="px-3 py-2.5 text-right">{inr(totals.invested, { precise: true })}</td>
              <td className="px-3 py-2.5 text-right">{inr(totals.value, { precise: true })}</td>
              <td className={cn("px-3 py-2.5 text-right", tone(totals.pnl))}>{inr(totals.pnl, { precise: true, signed: true })}</td>
              <td className={cn("px-3 py-2.5 text-right", tone(totals.pnlPct))}>{pct(totals.pnlPct, { signed: true })}</td>
              <td colSpan={3} />
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="lg:hidden">
        <div className="flex items-center justify-end gap-2 border-b border-border px-4 py-2 text-xs text-muted-foreground">
          <label htmlFor="mobile-sort">Sort</label>
          <select id="mobile-sort" value={sort.key}
            onChange={(e) => setSort({ key: e.target.value as SortKey, dir: e.target.value === "name" ? 1 : -1 })}
            className="h-8 rounded border border-border bg-surface px-2 text-foreground">
            <option value="value">Current value</option>
            <option value="pnl_pct">Returns (%)</option>
            <option value="day_change_pct">Day change</option>
            <option value="name">Name</option>
          </select>
        </div>
        <ul className="num divide-y divide-border/70">
          {rows.map((h) => (
            <li key={h.id} className="flex items-stretch">
              <Link href={holdingHref(h)} className="flex min-w-0 flex-1 items-center gap-3 py-3 pl-4">
                <span className="h-9 w-0.5 shrink-0 rounded-full" style={{ background: brokerColor(h.broker) }} aria-hidden />
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="truncate font-medium">{holdingTitle(h)}</span>
                    <span className="font-medium">{h.value === null ? <span className="text-text-tertiary">Awaiting price</span> : inr(h.value)}</span>
                  </div>
                  <div className="mt-0.5 flex items-baseline justify-between gap-2 text-xs">
                    <span className="truncate text-muted-foreground">{units(h)} {h.kind === "mf" ? "units" : "shares"} at {inr(h.avg_cost)}, {h.broker}</span>
                    {h.pnl !== null && <span className={tone(h.pnl)}>{inr(h.pnl, { signed: true })} ({pct(h.pnl_pct, { signed: true })})</span>}
                  </div>
                  <div className="mt-0.5 flex items-baseline justify-between gap-2 text-xs text-muted-foreground">
                    {h.close !== null && <span>LTP {inr(h.close, { precise: true })}</span>}
                    {h.day_change_pct !== null && <span className={tone(h.day_change_pct)}>{pct(h.day_change_pct, { signed: true })} today</span>}
                  </div>
                </div>
              </Link>
              <div className="flex w-11 items-center justify-center">
                {h.source === "manual" && (
                  <button type="button" onClick={() => onEdit(h)} aria-label={`Edit ${h.symbol} at ${h.broker}`}
                    className="grid size-11 place-items-center text-text-tertiary">
                    <PencilIcon className="size-4" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
