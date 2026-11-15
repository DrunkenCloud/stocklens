"use client";

import { ArrowDownIcon, ArrowUpIcon } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Panel } from "@/components/panel";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebounced } from "@/hooks/use-debounced";
import { inr, inrCompact, num, pct, tone } from "@/lib/format";
import { usePortfolio, useScreen } from "@/lib/queries";
import type { ScreenRow } from "@/lib/types";
import { cn } from "@/lib/utils";

type SortKey = "symbol" | "market_cap" | "pe" | "pb" | "roe" | "debt_to_equity" | "dividend_yield" | "rev_cagr_3y";

const COLUMNS: { key: SortKey | "latest_close"; label: string; render: (r: ScreenRow) => React.ReactNode }[] = [
  { key: "latest_close", label: "LTP", render: (r) => inr(r.latest_close, { precise: true }) },
  { key: "market_cap", label: "Market cap", render: (r) => inrCompact(r.market_cap) },
  { key: "pe", label: "P/E", render: (r) => num(r.pe, 1) },
  { key: "pb", label: "P/B", render: (r) => num(r.pb, 1) },
  { key: "roe", label: "ROE", render: (r) => pct(r.roe, { digits: 1 }) },
  { key: "debt_to_equity", label: "D/E", render: (r) => num(r.debt_to_equity, 2) },
  { key: "dividend_yield", label: "Div. yield", render: (r) => pct(r.dividend_yield) },
  { key: "rev_cagr_3y", label: "Rev CAGR 3Y", render: (r) => <span className={tone(r.rev_cagr_3y)}>{pct(r.rev_cagr_3y, { signed: true, digits: 1 })}</span> },
];

const FILTERS = [
  { key: "pe_max", label: "P/E at most", placeholder: "30" },
  { key: "roe_min", label: "ROE at least (%)", placeholder: "15" },
  { key: "de_max", label: "D/E at most", placeholder: "1" },
  { key: "div_yield_min", label: "Div. yield at least (%)", placeholder: "1" },
  { key: "rev_cagr_3y_min", label: "Rev CAGR 3Y at least (%)", placeholder: "10" },
] as const;

export default function ScreenerPage() {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sector, setSector] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({ key: "market_cap", dir: "desc" });
  const debounced = useDebounced(filters, 300);

  const params = useMemo(() => {
    const p = new URLSearchParams({ sort_by: sort.key, order: sort.dir, limit: "500" });
    for (const [k, v] of Object.entries(debounced)) if (v.trim() && !Number.isNaN(Number(v))) p.set(k, v.trim());
    if (sector) p.set("sector", sector);
    return p;
  }, [debounced, sector, sort]);

  const { data, isPending, isError, error, isFetching } = useScreen(params);
  const { data: portfolio } = usePortfolio();
  const held = useMemo(() => new Set(portfolio?.holdings.map((h) => h.symbol)), [portfolio]);
  const { data: allRows } = useScreen(new URLSearchParams({ limit: "500" }));
  const sectors = useMemo(() => [...new Set((allRows ?? []).map((r) => r.sector).filter(Boolean) as string[])].sort(), [allRows]);
  const activeCount = Object.values(filters).filter((v) => v.trim()).length + (sector ? 1 : 0);

  const toggleSort = (key: SortKey) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: key === "symbol" ? "asc" : "desc" }));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-lg font-medium">Screener</h1>
        <p className="text-xs text-muted-foreground">Filters every tracked stock on its latest fundamentals. Track more stocks from search.</p>
      </div>

      <Panel
        title="Filters"
        actions={activeCount > 0 && (
          <button type="button" onClick={() => { setFilters({}); setSector(""); }} className="text-xs text-accent-blue hover:underline">
            Clear {activeCount}
          </button>
        )}
      >
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {FILTERS.map((f) => (
            <label key={f.key} className="text-xs text-muted-foreground">
              {f.label}
              <Input
                inputMode="decimal"
                value={filters[f.key] ?? ""}
                placeholder={`e.g. ${f.placeholder}`}
                onChange={(e) => setFilters((cur) => ({ ...cur, [f.key]: e.target.value }))}
                className="num mt-1 h-8 placeholder:text-text-tertiary/70"
              />
            </label>
          ))}
          <label className="text-xs text-muted-foreground">
            Sector
            <select value={sector} onChange={(e) => setSector(e.target.value)}
              className="mt-1 h-8 w-full rounded-md border border-input bg-surface px-2 text-foreground">
              <option value="">All sectors</option>
              {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
        </div>
      </Panel>

      <Panel
        title={<>Results {data && <span className="font-normal text-muted-foreground">({data.length})</span>}</>}
        actions={isFetching && <span className="text-xs text-muted-foreground">Updating…</span>}
        bodyClassName="p-0"
      >
        {isPending ? (
          <Skeleton className="m-4 h-64" />
        ) : isError ? (
          <p className="p-6 text-loss">{error.message}</p>
        ) : data.length === 0 ? (
          <p className="p-10 text-center text-sm text-muted-foreground">No tracked stock matches these filters.</p>
        ) : (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="num w-full text-[13px]">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <SortHeader label="Company" sortKey="symbol" sort={sort} onSort={toggleSort} align="left" />
                    {COLUMNS.map((c) =>
                      c.key === "latest_close" ? (
                        <th key={c.key} scope="col" className="px-3 py-2 text-right font-normal">{c.label}</th>
                      ) : (
                        <SortHeader key={c.key} label={c.label} sortKey={c.key} sort={sort} onSort={toggleSort} />
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {data.map((r) => (
                    <tr key={r.symbol} className="group border-b border-border/70 last:border-0 hover:bg-muted/60">
                      <td className="py-2 pr-3 pl-4">
                        <Link href={`/stock/?s=${encodeURIComponent(r.symbol)}`} className="block">
                          <span className="flex items-center gap-1.5 font-medium group-hover:text-accent-blue">
                            {r.symbol}
                            {held.has(r.symbol) && <span className="rounded bg-muted px-1 text-[10px] font-normal text-muted-foreground">Held</span>}
                          </span>
                          <span className="block max-w-64 truncate text-[11px] text-muted-foreground">{r.name}{r.sector ? `, ${r.sector}` : ""}</span>
                        </Link>
                      </td>
                      {COLUMNS.map((c) => <td key={c.key} className="px-3 py-2 text-right">{c.render(r)}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ul className="num divide-y divide-border/70 md:hidden">
              {data.map((r) => (
                <li key={r.symbol}>
                  <Link href={`/stock/?s=${encodeURIComponent(r.symbol)}`} className="block px-4 py-3">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-medium">{r.symbol}{held.has(r.symbol) && <span className="ml-1.5 text-[10px] text-muted-foreground">Held</span>}</span>
                      <span>{inr(r.latest_close, { precise: true })}</span>
                    </div>
                    <div className="truncate text-xs text-muted-foreground">{r.name}</div>
                    <div className="mt-1.5 grid grid-cols-4 gap-2 text-xs">
                      <span><span className="text-muted-foreground">P/E </span>{num(r.pe, 1)}</span>
                      <span><span className="text-muted-foreground">ROE </span>{pct(r.roe, { digits: 0 })}</span>
                      <span><span className="text-muted-foreground">D/E </span>{num(r.debt_to_equity, 1)}</span>
                      <span className="text-right">{inrCompact(r.market_cap)}</span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </Panel>
    </div>
  );
}

function SortHeader({
  label, sortKey, sort, onSort, align = "right",
}: {
  label: string;
  sortKey: SortKey;
  sort: { key: SortKey; dir: "asc" | "desc" };
  onSort: (k: SortKey) => void;
  align?: "left" | "right";
}) {
  const active = sort.key === sortKey;
  return (
    <th scope="col" aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : undefined}
      className={cn("px-3 py-2 font-normal first:pl-4", align === "left" ? "text-left" : "text-right")}>
      <button type="button" onClick={() => onSort(sortKey)} className="inline-flex items-center gap-1 hover:text-foreground">
        {label}
        {active && (sort.dir === "asc" ? <ArrowUpIcon className="size-3" /> : <ArrowDownIcon className="size-3" />)}
      </button>
    </th>
  );
}
