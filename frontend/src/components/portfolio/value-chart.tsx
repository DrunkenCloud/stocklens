"use client";

import { useMemo, useState } from "react";

import { TimeSeriesChart, type SeriesPoint } from "@/components/charts/time-series-chart";
import { Panel, Segmented } from "@/components/panel";
import { Skeleton } from "@/components/ui/skeleton";
import { date, inr, pct, tone } from "@/lib/format";
import { usePortfolioHistory } from "@/lib/queries";
import type { Scope } from "@/lib/types";
import { cn } from "@/lib/utils";

const RANGES = [
  { value: "30", label: "1M" },
  { value: "182", label: "6M" },
  { value: "365", label: "1Y" },
  { value: "1095", label: "3Y" },
  { value: "1826", label: "5Y" },
  { value: "4380", label: "All" },
] as const;
type Range = (typeof RANGES)[number]["value"];

export function ValueChart({ pricedInvested, scope }: { pricedInvested: number; scope: Scope }) {
  const [range, setRange] = useState<Range>("365");
  const [hover, setHover] = useState<SeriesPoint | null>(null);
  const { data, isPending, isError } = usePortfolioHistory(Number(range), scope);
  const series = useMemo(() => (data ?? []).map((d) => ({ time: d.date, value: d.value })), [data]);
  const reference = useMemo(() => (pricedInvested ? { value: pricedInvested, label: "Invested" } : null), [pricedInvested]);

  const first = series[0]?.value;
  const shown = hover ?? series[series.length - 1];
  const change = shown && first ? shown.value - first : null;

  return (
    <Panel
      className="h-full"
      title="Value of your holdings"
      actions={<Segmented label="Time range" options={[...RANGES]} value={range} onChange={setRange} />}
      bodyClassName="p-0"
    >
      <div className="num flex flex-wrap items-baseline gap-x-3 px-4 pt-3">
        <span className="text-xl font-medium">{shown ? inr(shown.value) : "–"}</span>
        <span className={cn("text-sm", tone(change))}>
          {change !== null && `${inr(change, { signed: true })} (${pct((change / first) * 100, { signed: true })})`}
        </span>
        <span className="text-xs text-muted-foreground">{shown ? (hover ? date(shown.time) : `since ${date(series[0]?.time)}`) : ""}</span>
      </div>
      <div className="px-1 pb-1">
        {isPending ? (
          <Skeleton className="m-3 h-[248px]" />
        ) : isError || series.length < 2 ? (
          <p className="grid h-[260px] place-items-center px-6 text-center text-sm text-muted-foreground">
            {isError ? "Couldn't load the value history." : "Not enough price history yet for this range."}
          </p>
        ) : (
          <TimeSeriesChart data={series} height={260} reference={reference} onHover={setHover} />
        )}
      </div>
      <p className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
        What the shares you hold today were worth at each day&apos;s closing price. Earlier buys and sells aren&apos;t reflected.
      </p>
    </Panel>
  );
}
