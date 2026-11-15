"use client";

import { ArrowDownIcon, ArrowUpIcon, PencilIcon } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import type { Holding } from "@/lib/types";
import { brokerColor, inr, pct, qty, tone } from "@/lib/format";
import { cn } from "@/lib/utils";

type SortKey = "name" | "value" | "pnl_pct" | "day_change_pct" | "invested";

const COLUMNS: { key: SortKey | null; label: string; className?: string }[] = [
  { key: "name", label: "Stock" },
  { key: null, label: "Shares", className: "text-right" },
  { key: null, label: "Avg cost", className: "text-right" },
  { key: "day_change_pct", label: "Last price", className: "text-right" },
  { key: "invested", label: "Invested", className: "text-right" },
  { key: "value", label: "Value", className: "text-right" },
  { key: "pnl_pct", label: "Return", className: "text-right" },
];

function sortValue(h: Holding, key: SortKey): number | string {
  if (key === "name") return h.name.toLowerCase();
  return h[key] ?? Number.NEGATIVE_INFINITY;
}

export function HoldingsTable({ holdings, onEdit }: { holdings: Holding[]; onEdit: (h: Holding) => void }) {
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

  const toggleSort = (key: SortKey) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 1 ? -1 : 1 } : { key, dir: key === "name" ? 1 : -1 }));

  return (
    <div>
      {brokers.length > 1 && (
        <div className="mb-3 flex flex-wrap gap-1.5" role="group" aria-label="Filter by broker">
          {[null, ...brokers].map((b) => (
            <button
              key={b ?? "all"}
              type="button"
              aria-pressed={broker === b}
              onClick={() => setBroker(b)}
              className={cn(
                "flex items-center gap-1.5 rounded-full border border-border px-3 py-1 text-sm text-muted-foreground hover:text-foreground",
                broker === b && "border-foreground/30 bg-secondary text-foreground",
              )}
            >
              {b && <span className="size-2 rounded-full" style={{ background: brokerColor(b) }} aria-hidden />}
              {b ?? "All brokers"}
            </button>
          ))}
        </div>
      )}

      {/* Wide screens: a real table */}
      <div className="hidden overflow-x-auto md:block">
        <table className="num w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              {COLUMNS.map((c) => (
                <th key={c.label} scope="col" className={cn("py-2 pr-4 font-normal last:pr-0", c.className)}
                  aria-sort={c.key && sort.key === c.key ? (sort.dir === 1 ? "ascending" : "descending") : undefined}>
                  {c.key ? (
                    <button type="button" onClick={() => toggleSort(c.key!)} className="inline-flex items-center gap-1 hover:text-foreground">
                      {c.label}
                      {sort.key === c.key && (sort.dir === 1 ? <ArrowUpIcon className="size-3" /> : <ArrowDownIcon className="size-3" />)}
                    </button>
                  ) : c.label}
                </th>
              ))}
              <th className="w-8"><span className="sr-only">Edit</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              <tr key={h.id} className="border-b border-border/70 last:border-0 hover:bg-secondary/50">
                <td className="py-2.5 pr-4">
                  <Link href={`/stock?s=${encodeURIComponent(h.symbol)}`} className="group flex items-center gap-2.5">
                    <span className="size-2 shrink-0 rounded-full" style={{ background: brokerColor(h.broker) }} title={h.broker} />
                    <span className="min-w-0">
                      <span className="block truncate font-medium group-hover:underline">{h.name}</span>
                      <span className="block text-xs text-muted-foreground">
                        {h.symbol} at {h.broker}{h.source === "icici_sync" && ", synced"}
                      </span>
                    </span>
                  </Link>
                </td>
                <td className="py-2.5 pr-4 text-right">{qty(h.quantity)}</td>
                <td className="py-2.5 pr-4 text-right">{inr(h.avg_cost, { precise: true })}</td>
                <td className="py-2.5 pr-4 text-right">
                  {h.close === null ? <span className="text-muted-foreground">Loading</span> : (
                    <>
                      <div>{inr(h.close, { precise: true })}</div>
                      <div className={cn("text-xs", tone(h.day_change_pct))}>{pct(h.day_change_pct, { signed: true })}</div>
                    </>
                  )}
                </td>
                <td className="py-2.5 pr-4 text-right">{inr(h.invested)}</td>
                <td className="py-2.5 pr-4 text-right font-medium">{inr(h.value)}</td>
                <td className={cn("py-2.5 text-right", tone(h.pnl))}>
                  {h.pnl === null ? "–" : (
                    <>
                      <div>{inr(h.pnl, { signed: true })}</div>
                      <div className="text-xs">{pct(h.pnl_pct, { signed: true })}</div>
                    </>
                  )}
                </td>
                <td className="py-2.5 pl-2 text-right">
                  {h.source === "manual" && (
                    <button type="button" onClick={() => onEdit(h)} aria-label={`Edit ${h.name} at ${h.broker}`}
                      className="rounded p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground">
                      <PencilIcon className="size-3.5" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Phones: one line per holding, value and return on the right */}
      <div className="md:hidden">
        <label className="mb-2 flex items-center justify-end gap-2 text-sm text-muted-foreground">
          Sort by
          <select value={sort.key} onChange={(e) => setSort({ key: e.target.value as SortKey, dir: e.target.value === "name" ? 1 : -1 })}
            className="rounded-md border border-input bg-surface px-2 py-1 text-foreground">
            <option value="value">Value</option>
            <option value="pnl_pct">Return</option>
            <option value="day_change_pct">Last day</option>
            <option value="name">Name</option>
          </select>
        </label>
        <ul className="num divide-y divide-border/70 border-y border-border/70">
          {rows.map((h) => (
            <li key={h.id} className="flex items-center gap-3 py-3">
              <span className="size-2 shrink-0 rounded-full" style={{ background: brokerColor(h.broker) }} aria-hidden />
              <Link href={`/stock?s=${encodeURIComponent(h.symbol)}`} className="min-w-0 flex-1">
                <div className="truncate font-medium">{h.name}</div>
                <div className="text-xs text-muted-foreground">
                  {qty(h.quantity)} × {inr(h.avg_cost)} at {h.broker}
                </div>
              </Link>
              <div className="text-right">
                <div className="font-medium">{h.value === null ? <span className="text-muted-foreground">Loading</span> : inr(h.value)}</div>
                <div className={cn("text-xs", tone(h.pnl))}>{pct(h.pnl_pct, { signed: true })}</div>
              </div>
              {h.source === "manual" && (
                <button type="button" onClick={() => onEdit(h)} aria-label={`Edit ${h.name} at ${h.broker}`}
                  className="-mr-1 rounded p-2 text-muted-foreground">
                  <PencilIcon className="size-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
