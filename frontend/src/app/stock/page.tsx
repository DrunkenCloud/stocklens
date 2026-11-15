"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useMemo } from "react";
import { toast } from "sonner";

import { RangeBar } from "@/components/charts/range-bar";
import { Panel } from "@/components/panel";
import { Fundamentals } from "@/components/stock/fundamentals";
import { PricePanel } from "@/components/stock/price-panel";
import { ReturnsPanel } from "@/components/stock/returns-panel";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { brokerColor, date, inr, num, pct, qty, tone } from "@/lib/format";
import { usePortfolio, usePrices, useSecuritySearch, useStock, useTrack } from "@/lib/queries";
import type { PricePoint, Stock } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function StockPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <StockView />
    </Suspense>
  );
}

function StockView() {
  const params = useSearchParams();
  const symbol = (params.get("s") ?? "").toUpperCase();
  const isin = params.get("isin") ?? "";
  const stock = useStock(symbol);

  if (!symbol && !isin) return <p className="py-16 text-muted-foreground">Search for a stock using the bar at the top.</p>;
  if (symbol && stock.isPending) return <Skeleton className="h-96 w-full" />;
  if (!symbol || stock.error?.message.includes("isn't tracked")) return <Untracked query={symbol || isin} />;
  if (stock.isError) return <p className="py-16 text-loss">{stock.error.message}</p>;
  return <Tracked stock={stock.data!} />;
}

function Tracked({ stock }: { stock: Stock }) {
  const prices = usePrices(stock.symbol, "2010-01-01");
  const lp = stock.latest_price;
  const dayChange = lp?.prev_close ? lp.close - lp.prev_close : null;

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-xl font-medium tracking-tight">{stock.name}</h1>
          <div className="mt-1 flex flex-wrap gap-x-3 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">{stock.symbol}</span>
            <span>{stock.exchanges.join(", ")}</span>
            {stock.sector && <span>{stock.sector}</span>}
          </div>
        </div>
        {lp && (
          <div className="num text-right">
            <div className="text-3xl font-medium tracking-tight">{inr(lp.close, { precise: true })}</div>
            <div className={cn("text-sm", tone(dayChange))}>
              {dayChange !== null && `${inr(dayChange, { signed: true, precise: true })} (${pct((dayChange / lp.prev_close!) * 100, { signed: true })})`}
              <span className="ml-2 text-xs text-muted-foreground">close on {date(lp.date)}</span>
            </div>
          </div>
        )}
      </header>

      <PricePanel prices={prices.data} isPending={prices.isPending} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Performance prices={prices.data} />
        <Position symbol={stock.symbol} />
      </div>

      <Fundamentals data={stock.fundamentals} />
      <ReturnsPanel symbol={stock.symbol} />
    </div>
  );
}

function Performance({ prices }: { prices: PricePoint[] | undefined }) {
  const stats = useMemo(() => {
    if (!prices?.length) return null;
    const last = prices[prices.length - 1];
    const prev = prices[prices.length - 2];
    const yearAgo = new Date(last.date);
    yearAgo.setFullYear(yearAgo.getFullYear() - 1);
    const cutoff = yearAgo.toISOString().slice(0, 10);
    const year = prices.filter((p) => p.date >= cutoff);
    return {
      last,
      prevClose: prev?.close ?? null,
      low52: Math.min(...year.map((p) => p.low ?? p.close)),
      high52: Math.max(...year.map((p) => p.high ?? p.close)),
      return52: year.length > 1 ? ((last.close - year[0].close) / year[0].close) * 100 : null,
    };
  }, [prices]);

  return (
    <Panel title="Performance">
      {!stats ? (
        <p className="py-6 text-center text-sm text-muted-foreground">Waiting for price history.</p>
      ) : (
        <div className="space-y-5">
          {stats.last.low !== null && stats.last.high !== null && (
            <RangeBar label={`Day's range, ${date(stats.last.date)}`} low={stats.last.low} high={stats.last.high} current={stats.last.close} />
          )}
          <RangeBar label="52-week range" low={stats.low52} high={stats.high52} current={stats.last.close} />
          <dl className="num grid grid-cols-2 gap-4 border-t border-border pt-4 sm:grid-cols-4">
            <div><dt className="text-xs text-muted-foreground">Open</dt><dd className="mt-0.5">{inr(stats.last.open, { precise: true })}</dd></div>
            <div><dt className="text-xs text-muted-foreground">Prev. close</dt><dd className="mt-0.5">{inr(stats.prevClose, { precise: true })}</dd></div>
            <div><dt className="text-xs text-muted-foreground">Volume</dt><dd className="mt-0.5">{num(stats.last.volume, 0)}</dd></div>
            <div><dt className="text-xs text-muted-foreground">1Y return</dt><dd className={cn("mt-0.5", tone(stats.return52))}>{pct(stats.return52, { signed: true })}</dd></div>
          </dl>
        </div>
      )}
    </Panel>
  );
}

function Position({ symbol }: { symbol: string }) {
  const { data, isPending } = usePortfolio();
  const lots = data?.holdings.filter((h) => h.symbol === symbol) ?? [];
  if (isPending) return <Skeleton className="h-36" />;
  if (!lots.length) {
    return (
      <Panel title="Your position">
        <p className="py-6 text-center text-sm text-muted-foreground">You don&apos;t hold {symbol} in any account.</p>
      </Panel>
    );
  }
  const quantity = lots.reduce((s, h) => s + h.quantity, 0);
  const invested = lots.reduce((s, h) => s + h.invested, 0);
  const value = lots.every((h) => h.value !== null) ? lots.reduce((s, h) => s + (h.value ?? 0), 0) : null;
  const pnl = value !== null ? value - invested : null;

  return (
    <Panel title="Your position">
      <dl className="num grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div><dt className="text-xs text-muted-foreground">Shares</dt><dd className="mt-0.5 text-[15px] font-medium">{qty(quantity)}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Avg cost</dt><dd className="mt-0.5 text-[15px] font-medium">{inr(invested / quantity, { precise: true })}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Current value</dt><dd className="mt-0.5 text-[15px] font-medium">{inr(value)}</dd></div>
        <div>
          <dt className="text-xs text-muted-foreground">Returns</dt>
          <dd className={cn("mt-0.5 text-[15px] font-medium", tone(pnl))}>{pnl === null ? "–" : `${inr(pnl, { signed: true })} (${pct((pnl / invested) * 100, { signed: true })})`}</dd>
        </div>
      </dl>
      {lots.length > 1 && (
        <ul className="num mt-4 space-y-1.5 border-t border-border pt-3 text-[13px]">
          {lots.map((h) => (
            <li key={h.id} className="flex items-center gap-2">
              <span className="size-2 rounded-full" style={{ background: brokerColor(h.broker) }} aria-hidden />
              <span className="flex-1">{h.broker}</span>
              <span className="text-muted-foreground">{qty(h.quantity)} at {inr(h.avg_cost)}</span>
              <span className={cn("w-16 text-right", tone(h.pnl))}>{pct(h.pnl_pct, { signed: true })}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function Untracked({ query }: { query: string }) {
  const { data, isPending } = useSecuritySearch(query);
  const track = useTrack();
  const security = data?.find((s) => s.nse_symbol === query || s.isin === query);

  if (isPending) return <Skeleton className="h-40 w-full" />;
  if (!security) return <p className="py-16 text-muted-foreground">No listed stock matches “{query}”.</p>;

  return (
    <Panel>
      <div className="flex flex-wrap items-center justify-between gap-4 py-2">
        <div>
          <h1 className="text-xl font-medium tracking-tight">{security.name}</h1>
          <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">{security.nse_symbol ?? security.bse_symbol}</span>
            <span>{security.exchanges.join(", ")}</span>
            {security.bse_code && <span>BSE {security.bse_code}</span>}
            <span>{security.isin}</span>
          </div>
        </div>
        {security.nse_symbol ? (
          <Button
            disabled={track.isPending}
            onClick={() =>
              track.mutate(security.isin, {
                onSuccess: () => toast.success(`Tracking ${security.nse_symbol}. Price history and fundamentals are loading.`),
                onError: (e) => toast.error(e.message),
              })
            }
          >
            {track.isPending ? "Adding…" : "Track this stock"}
          </Button>
        ) : (
          <p className="max-w-xs text-sm text-muted-foreground">Listed only on BSE. Prices come from NSE, so it can&apos;t be tracked yet.</p>
        )}
      </div>
      <p className="mt-2 border-t border-border pt-3 text-sm text-muted-foreground">
        Tracking a stock loads its price history and fundamentals, adds it to the screener, and lets you add it as a holding.
      </p>
    </Panel>
  );
}
