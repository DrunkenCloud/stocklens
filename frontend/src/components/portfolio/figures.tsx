import type { Portfolio } from "@/lib/types";
import { inr, pct, tone } from "@/lib/format";
import { cn } from "@/lib/utils";

function Figure({ label, value, change, className }: { label: string; value: string; change?: { v: number | null; pct: number | null }; className?: string }) {
  return (
    <div className={cn("px-4 py-3", className)}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="num mt-1 text-lg font-medium">
        {change ? <span className={tone(change.v)}>{value}</span> : value}
      </div>
      {change && <div className={cn("num text-xs", tone(change.v))}>{pct(change.pct, { signed: true })}</div>}
    </div>
  );
}

export function Figures({ portfolio }: { portfolio: Portfolio }) {
  const t = portfolio.totals;
  return (
    <section aria-label="Portfolio summary" className="rounded-md border border-border bg-surface">
      <div className="border-b border-border px-4 pt-4 pb-3 md:hidden">
        <div className="text-xs text-muted-foreground">Current value</div>
        <div className="num mt-1 text-3xl font-medium tracking-tight">{inr(t.value)}</div>
      </div>
      <div className="grid grid-cols-2 divide-x divide-border sm:grid-cols-4 md:grid-cols-5 [&>*:nth-child(n+3)]:border-t sm:[&>*:nth-child(n+3)]:border-t-0">
        <div className="hidden px-4 py-3 md:block">
          <div className="text-xs text-muted-foreground">Current value</div>
          <div className="num mt-1 text-2xl font-medium tracking-tight">{inr(t.value)}</div>
        </div>
        <Figure label="Invested" value={inr(t.invested)} />
        <Figure label="Total returns" value={inr(t.pnl, { signed: true })} change={{ v: t.pnl, pct: t.pnl_pct }} />
        <Figure label="1D returns" value={inr(t.day_change, { signed: true })} change={{ v: t.day_change, pct: t.day_change_pct }} />
        <div className="px-4 py-3">
          <div className="text-xs text-muted-foreground">XIRR</div>
          <div className={cn("num mt-1 text-lg font-medium", tone(t.xirr))}>{t.xirr === null ? "–" : pct(t.xirr, { signed: true })}</div>
          {t.xirr_coverage_pct !== null && t.xirr_coverage_pct < 99.5 && (
            <div className="num text-xs text-muted-foreground">on {pct(t.xirr_coverage_pct, { digits: 0 })} with dates</div>
          )}
        </div>
      </div>
    </section>
  );
}
