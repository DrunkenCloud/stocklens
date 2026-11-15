"use client";

import { useState } from "react";

import { Panel, Segmented } from "@/components/panel";
import { Input } from "@/components/ui/input";
import { useDebounced } from "@/hooks/use-debounced";
import { date, inr, pct, tone } from "@/lib/format";
import { useReturns } from "@/lib/queries";
import { cn } from "@/lib/utils";

const PERIODS = [
  { value: "1", label: "1Y" },
  { value: "3", label: "3Y" },
  { value: "5", label: "5Y" },
  { value: "10", label: "10Y" },
] as const;

function yearsAgo(years: number) {
  const d = new Date();
  d.setFullYear(d.getFullYear() - years);
  return d.toISOString().slice(0, 10);
}

function Stat({ label, value, className }: { label: string; value: string; className?: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("mt-0.5 text-[15px] font-medium", className)}>{value}</div>
    </div>
  );
}

export function ReturnsPanel({ symbol }: { symbol: string }) {
  const [years, setYears] = useState<(typeof PERIODS)[number]["value"]>("5");
  const [amount, setAmount] = useState("100000");
  const debouncedAmount = Number(useDebounced(amount, 300)) || 0;
  const { data, isError, error } = useReturns(symbol, yearsAgo(Number(years)), debouncedAmount);

  return (
    <Panel title="If you had invested" actions={<Segmented label="Period" options={[...PERIODS]} value={years} onChange={setYears} />}>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-4">
        <label className="w-40">
          <span className="text-xs text-muted-foreground">Amount (₹)</span>
          <Input inputMode="numeric" value={amount} onChange={(e) => setAmount(e.target.value.replace(/[^\d]/g, ""))} className="num mt-1" />
        </label>
        {isError ? (
          <p className="text-sm text-muted-foreground">{error.message}</p>
        ) : data ? (
          <div className="num grid flex-1 grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-6">
            <Stat label={`Worth on ${date(data.date_end)}`} value={inr(data.value_now)} className={tone(data.value_now - data.amount_invested)} />
            <Stat label="Total return" value={pct(data.total_return_pct, { signed: true })} className={tone(data.total_return_pct)} />
            <Stat label="CAGR" value={data.cagr_pct === null ? "N/A" : pct(data.cagr_pct, { signed: true })} className={tone(data.cagr_pct)} />
            <Stat label="Max drawdown" value={pct(data.max_drawdown_pct)} className="text-loss" />
            <Stat label={`Best year (${data.best_year.year})`} value={pct(data.best_year.return_pct, { signed: true })} className={tone(data.best_year.return_pct)} />
            <Stat label={`Worst year (${data.worst_year.year})`} value={pct(data.worst_year.return_pct, { signed: true })} className={tone(data.worst_year.return_pct)} />
          </div>
        ) : null}
      </div>
      {data && (
        <p className="mt-4 text-[11px] text-muted-foreground">
          Bought at {inr(data.close_start, { precise: true })} on {date(data.date_start)}. Price change only: dividends aren&apos;t included. Past returns describe what happened, not what will.
        </p>
      )}
    </Panel>
  );
}
