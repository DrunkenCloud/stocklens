"use client";

import { useMemo, useState } from "react";

import { TimeSeriesChart, type SeriesPoint } from "@/components/charts/time-series-chart";
import { Panel, Segmented } from "@/components/panel";
import { Skeleton } from "@/components/ui/skeleton";
import { date, inr, inrCompact, pct, tone } from "@/lib/format";
import { usePortfolioGrowth } from "@/lib/queries";
import type { Scope } from "@/lib/types";
import { cn } from "@/lib/utils";

const RANGES = [
  { value: "30", label: "1M" },
  { value: "182", label: "6M" },
  { value: "365", label: "1Y" },
  { value: "1095", label: "3Y" },
  { value: "10950", label: "All" },
] as const;
type Range = (typeof RANGES)[number]["value"];

export function GrowthChart({ scope }: { scope: Scope }) {
  const [range, setRange] = useState<Range>("10950");
  const [hover, setHover] = useState<string | null>(null);
  const { data, isPending, isError } = usePortfolioGrowth(Number(range), scope);

  const { value, invested, byDate } = useMemo(() => {
    const series = data?.series ?? [];
    return {
      value: series.map((p) => ({ time: p.date, value: p.value })),
      invested: series.map((p) => ({ time: p.date, value: p.invested })),
      byDate: new Map(series.map((p) => [p.date, p])),
    };
  }, [data]);

  const shown = (hover && byDate.get(hover)) || data?.series[data.series.length - 1];
  const gain = shown ? shown.value - shown.invested : null;

  return (
    <Panel
      className="h-full"
      title="Your money over time"
      actions={<Segmented label="Time range" options={[...RANGES]} value={range} onChange={setRange} />}
      bodyClassName="p-0"
    >
      <div className="num flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 pt-3">
        <span className="text-xl font-medium">{shown ? inr(shown.value) : "–"}</span>
        <span className="text-sm text-muted-foreground">{shown ? `${inr(shown.invested)} invested` : ""}</span>
        <span className={cn("text-sm", tone(gain))}>
          {shown && gain !== null && `${inr(gain, { signed: true })} (${pct(shown.invested ? (gain / shown.invested) * 100 : null, { signed: true })})`}
        </span>
        <span className="text-xs text-muted-foreground">{shown ? date(shown.date) : ""}</span>
      </div>
      <div className="px-1 pb-1">
        {isPending ? (
          <Skeleton className="m-3 h-[248px]" />
        ) : isError || value.length < 2 ? (
          <p className="grid h-[260px] place-items-center px-6 text-center text-sm text-muted-foreground">
            {isError ? "Couldn't load your history." : "Add dated buys to see how your money grew."}
          </p>
        ) : (
          <TimeSeriesChart data={value} secondary={invested} height={260} onHover={(p: SeriesPoint | null) => setHover(p?.time ?? null)} />
        )}
      </div>
      <p className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
        Shaded: what your holdings were worth each day. Dashed: what you had put in.
        {data && data.excluded_count > 0 &&
          ` ${data.excluded_count} holding${data.excluded_count > 1 ? "s" : ""} without purchase dates (${inrCompact(data.excluded_invested)} invested) left out; add dates on their pages to include them.`}
      </p>
    </Panel>
  );
}
