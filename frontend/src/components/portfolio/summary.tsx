"use client";

import type { Portfolio, Status } from "@/lib/types";
import { ago, brokerColor, date, inr, inrCompact, pct, tone } from "@/lib/format";
import { cn } from "@/lib/utils";

/** The top of the page: what it's all worth, and how it's split across brokers. */
export function Summary({ portfolio, status }: { portfolio: Portfolio; status?: Status }) {
  const t = portfolio.totals;
  const unpriced = portfolio.holdings.filter((h) => h.value === null).length;
  const brokers = portfolio.by_broker;
  const barBase = brokers.reduce((s, b) => s + (b.value || b.invested), 0);

  return (
    <section aria-labelledby="summary-heading" className="space-y-6">
      <div className="space-y-2">
        <h1 id="summary-heading" className="text-sm font-medium text-muted-foreground" style={{ fontFamily: "var(--font-sans)" }}>
          Your holdings
        </h1>
        <p className="num font-heading text-5xl font-semibold tracking-tight sm:text-6xl">{inr(t.value)}</p>
        <div className="num flex flex-wrap gap-x-6 gap-y-1 text-[15px]">
          <span className={tone(t.pnl)}>
            {inr(t.pnl, { signed: true })} ({pct(t.pnl_pct, { signed: true })}) overall
          </span>
          <span className={tone(t.day_change)}>
            {inr(t.day_change, { signed: true })} ({pct(t.day_change_pct, { signed: true })}) on the last trading day
          </span>
          <span className="text-muted-foreground">{inr(t.invested)} invested</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Prices as of {date(status?.prices_as_of)}
          {status?.last_sync?.status === "done" && <>, ICICI synced {ago(status.last_sync.finished_at)}</>}
          {unpriced > 0 && <>. {unpriced} holding{unpriced > 1 ? "s" : ""} still waiting for a price, so not counted in value or returns.</>}
        </p>
      </div>

      {brokers.length > 0 && (
        <div>
          <div className="flex h-3 w-full overflow-hidden rounded-full bg-secondary" role="img"
            aria-label={brokers.map((b) => `${b.broker} ${inrCompact(b.value || b.invested)}`).join(", ")}>
            {brokers.map((b) => (
              <div key={b.broker} style={{ width: `${((b.value || b.invested) / barBase) * 100}%`, background: brokerColor(b.broker) }}
                className="h-full border-r-2 border-background last:border-r-0" />
            ))}
          </div>
          <ul className="mt-3 grid grid-cols-2 gap-x-6 gap-y-3 sm:flex sm:flex-wrap">
            {brokers.map((b) => (
              <li key={b.broker} className="min-w-0">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span className="size-2.5 shrink-0 rounded-full" style={{ background: brokerColor(b.broker) }} aria-hidden />
                  {b.broker}
                  <span className="text-xs">{b.count} stock{b.count > 1 ? "s" : ""}</span>
                </div>
                <div className="num mt-0.5 flex items-baseline gap-2">
                  {b.pnl === null ? (
                    <span className="text-muted-foreground">{inrCompact(b.invested)} invested</span>
                  ) : (
                    <>
                      <span className="font-medium">{inrCompact(b.value)}</span>
                      <span className={cn("text-sm", tone(b.pnl))}>{pct(b.pnl_pct, { signed: true })}</span>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
