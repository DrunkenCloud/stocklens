"use client";

import { useMemo, useState } from "react";

import { TimeSeriesChart, type SeriesPoint } from "@/components/charts/time-series-chart";
import { Panel, Segmented } from "@/components/panel";
import { Skeleton } from "@/components/ui/skeleton";
import { date, inr, pct, tone } from "@/lib/format";
import type { PricePoint } from "@/lib/types";
import { cn } from "@/lib/utils";

const RANGES = [
  { value: "7", label: "1W" },
  { value: "30", label: "1M" },
  { value: "91", label: "3M" },
  { value: "182", label: "6M" },
  { value: "365", label: "1Y" },
  { value: "1095", label: "3Y" },
  { value: "1826", label: "5Y" },
  { value: "all", label: "All" },
] as const;
type Range = (typeof RANGES)[number]["value"];

function sinceDays(prices: PricePoint[], days: number) {
  if (!prices.length) return prices;
  const last = new Date(prices[prices.length - 1].date);
  last.setDate(last.getDate() - days);
  const cutoff = last.toISOString().slice(0, 10);
  return prices.filter((p) => p.date >= cutoff);
}

export function PricePanel({ prices, isPending }: { prices: PricePoint[] | undefined; isPending: boolean }) {
  const [range, setRange] = useState<Range>("365");
  const [hover, setHover] = useState<SeriesPoint | null>(null);

  const series = useMemo(() => {
    const all = prices ?? [];
    const slice = range === "all" ? all : sinceDays(all, Number(range));
    return slice.map((p) => ({ time: p.date, value: p.close }));
  }, [prices, range]);

  const first = series[0]?.value;
  const shown = hover ?? series[series.length - 1];
  const change = shown && first ? shown.value - first : null;
  const label = RANGES.find((r) => r.value === range)?.label;

  return (
    <Panel
      title="Price"
      actions={<Segmented label="Time range" options={[...RANGES]} value={range} onChange={setRange} />}
      bodyClassName="p-0"
    >
      <div className="num flex flex-wrap items-baseline gap-x-3 px-4 pt-3">
        <span className="text-xl font-medium">{shown ? inr(shown.value, { precise: true }) : "–"}</span>
        <span className={cn("text-sm", tone(change))}>
          {change !== null && `${inr(change, { signed: true, precise: true })} (${pct((change / first) * 100, { signed: true })})`}
        </span>
        <span className="text-xs text-muted-foreground">{hover ? date(hover.time) : label === "All" ? "all available history" : `past ${label}`}</span>
      </div>
      <div className="px-1 pb-1">
        {isPending ? (
          <Skeleton className="m-3 h-[308px]" />
        ) : series.length < 2 ? (
          <p className="grid h-[320px] place-items-center text-sm text-muted-foreground">No price history yet. It loads after the next ICICI sync.</p>
        ) : (
          <TimeSeriesChart data={series} height={320} onHover={setHover} formatPrice={(v) => inr(v)} />
        )}
      </div>
    </Panel>
  );
}
