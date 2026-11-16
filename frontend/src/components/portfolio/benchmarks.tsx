"use client";

import { Panel } from "@/components/panel";
import { Skeleton } from "@/components/ui/skeleton";
import { date, inr, num, pct, tone } from "@/lib/format";
import { useBenchmarks } from "@/lib/queries";
import { cn } from "@/lib/utils";

function Change({ v }: { v: number | null }) {
  return <span className={cn("num", tone(v))}>{pct(v, { signed: true, digits: 1 })}</span>;
}

export function Benchmarks() {
  const { data, isPending, isError } = useBenchmarks();
  if (isError) return null;
  const p = data?.portfolio;

  return (
    <Panel title="You vs indexes" bodyClassName="p-0">
      {isPending || !data || !p ? (
        <Skeleton className="m-4 h-40" />
      ) : (
        <>
          <div className="border-b border-border px-4 py-3 text-sm">
            <span className="text-muted-foreground">Your XIRR </span>
            <span className={cn("num font-medium", tone(p.xirr))}>{pct(p.xirr, { signed: true, digits: 1 })}</span>
            <span className="text-muted-foreground"> on {inr(p.invested)} put in since {date(p.first_date)}, now worth </span>
            <span className="num font-medium">{inr(p.value)}</span>
          </div>
          <table className="hidden w-full text-sm lg:table">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="px-4 py-2 text-left font-normal">Index</th>
                <th className="px-2 py-2 text-right font-normal">Level</th>
                <th className="px-2 py-2 text-right font-normal">1D</th>
                <th className="px-2 py-2 text-right font-normal">1M</th>
                <th className="px-2 py-2 text-right font-normal">1Y</th>
                <th className="px-2 py-2 text-right font-normal">Same money in it</th>
                <th className="px-4 py-2 text-right font-normal">XIRR</th>
              </tr>
            </thead>
            <tbody>
              {data.indices.map((i) => (
                <tr key={i.symbol} className="border-b border-border last:border-0">
                  <td className="px-4 py-2">{i.name}</td>
                  <td className="num px-2 py-2 text-right">{num(i.close, 0)}</td>
                  <td className="px-2 py-2 text-right"><Change v={i.day_pct} /></td>
                  <td className="px-2 py-2 text-right"><Change v={i.month_pct} /></td>
                  <td className="px-2 py-2 text-right"><Change v={i.year_pct} /></td>
                  <td className="num px-2 py-2 text-right">{inr(i.value)}</td>
                  <td className="px-4 py-2 text-right"><Change v={i.xirr} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <ul className="divide-y divide-border lg:hidden">
            {data.indices.map((i) => (
              <li key={i.symbol} className="px-4 py-2.5 text-sm">
                <div className="flex justify-between gap-2">
                  <span>{i.name}</span>
                  <span className="text-xs text-muted-foreground">XIRR <Change v={i.xirr} /></span>
                </div>
                <div className="mt-0.5 flex gap-3 text-xs text-muted-foreground">
                  <span className="num">{num(i.close, 0)}</span>
                  <span>1D <Change v={i.day_pct} /></span>
                  <span>1M <Change v={i.month_pct} /></span>
                  <span>1Y <Change v={i.year_pct} /></span>
                </div>
              </li>
            ))}
          </ul>
          <p className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
            &ldquo;Same money in it&rdquo; replays every dated buy and sell into the index on the same day. Price indexes leave out
            dividends (about 1–1.5% a year).
            {p.coverage_pct !== null && p.coverage_pct < 99.5 && ` Holdings with undated entries are left out of both sides (${pct(100 - p.coverage_pct, { digits: 0 })} of invested).`}
          </p>
        </>
      )}
    </Panel>
  );
}
