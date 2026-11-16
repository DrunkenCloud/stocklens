"use client";

import Link from "next/link";

import { Panel } from "@/components/panel";
import { Skeleton } from "@/components/ui/skeleton";
import { date, inr, pct, tone } from "@/lib/format";
import { holdingHref, shortFundName } from "@/lib/holding";
import { useInsights } from "@/lib/queries";
import type { AssetRef } from "@/lib/types";
import { cn } from "@/lib/utils";

function List({ title, rows }: { title: string; rows: (AssetRef & { change: number })[] }) {
  return (
    <div>
      <div className="mb-1 text-xs text-muted-foreground">{title}</div>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">None</p>
      ) : (
        <ul className="space-y-1">
          {rows.map((r) => (
            <li key={`${r.kind}:${r.symbol}:${r.broker}`} className="flex justify-between gap-2 text-sm">
              <Link href={holdingHref(r)} className="truncate hover:underline">
                {r.kind === "mf" ? shortFundName(r.name) : r.symbol}
                <span className="ml-1 text-xs text-muted-foreground">{r.broker}</span>
              </Link>
              <span className={cn("num shrink-0", tone(r.change))}>{inr(r.change, { signed: true })}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function Movers() {
  const { data, isPending, isError } = useInsights();
  if (isError) return null;
  const dd = data?.drawdown;

  return (
    <Panel title="This month">
      {isPending || !data ? (
        <Skeleton className="h-40" />
      ) : (
        <div className="space-y-4">
          {dd && (
            <div>
              <div className="text-xs text-muted-foreground">Drop from peak</div>
              <div className={cn("num text-lg font-medium", tone(dd.current_pct < -0.05 ? dd.current_pct : 0))}>
                {dd.current_pct < -0.05 ? pct(dd.current_pct, { digits: 1 }) : "At its peak"}
              </div>
              <div className="text-xs text-muted-foreground">
                Peak {date(dd.peak_date)} · worst drop {pct(dd.max_pct, { digits: 1 })}, net of money added or taken out
              </div>
            </div>
          )}
          <List title={`Gained most since ${date(data.month_start)}`} rows={data.movers.up} />
          <List title="Lost most" rows={data.movers.down} />
        </div>
      )}
    </Panel>
  );
}
