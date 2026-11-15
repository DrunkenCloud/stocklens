"use client";

import { PencilIcon, PlusIcon } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";

import { MfForm, type MfFormTarget } from "@/components/mf/mf-form";
import { Panel } from "@/components/panel";
import { PricePanel } from "@/components/stock/price-panel";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ASSET_CLASS, brokerColor, date, inr, num, pct, tone } from "@/lib/format";
import { useFund, usePortfolio } from "@/lib/queries";
import type { Fund, PricePoint } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function FundPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <FundView />
    </Suspense>
  );
}

const PERIODS: { label: string; days: number }[] = [
  { label: "1M", days: 30 },
  { label: "6M", days: 182 },
  { label: "1Y", days: 365 },
  { label: "3Y", days: 1095 },
  { label: "5Y", days: 1826 },
];

function trailingReturns(navs: Fund["navs"]) {
  if (navs.length < 2) return [];
  const last = navs[navs.length - 1];
  const end = new Date(last.date).getTime();
  return PERIODS.map((p) => {
    const cutoff = end - p.days * 86_400_000;
    const start = navs.find((n) => new Date(n.date).getTime() >= cutoff);
    if (!start || new Date(navs[0].date).getTime() > cutoff + 7 * 86_400_000) return { ...p, value: null, annualised: false };
    const growth = last.nav / start.nav;
    const years = p.days / 365;
    return { ...p, value: years > 1 ? (Math.pow(growth, 1 / years) - 1) * 100 : (growth - 1) * 100, annualised: years > 1 };
  });
}

function FundView() {
  const code = Number(useSearchParams().get("code") ?? 0);
  const { data: fund, isPending, isError, error } = useFund(code);
  const { data: portfolio } = usePortfolio("mf");
  const [form, setForm] = useState<{ open: boolean; target: MfFormTarget }>({ open: false, target: {} });

  const prices = useMemo<PricePoint[]>(
    () => (fund?.navs ?? []).map((n) => ({ date: n.date, open: null, high: null, low: null, close: n.nav, volume: null })),
    [fund],
  );
  const returns = useMemo(() => trailingReturns(fund?.navs ?? []), [fund]);

  if (!code) return <p className="py-16 text-muted-foreground">Search for a fund using the bar at the top.</p>;
  if (isPending) return <Skeleton className="h-96 w-full" />;
  if (isError) return <p className="py-16 text-loss">{error.message}</p>;

  const navs = fund.navs;
  const last = navs[navs.length - 1];
  const prev = navs[navs.length - 2];
  const change = last && prev ? last.nav - prev.nav : null;
  const lots = portfolio?.holdings.filter((h) => h.kind === "mf" && h.symbol === String(code)) ?? [];
  const picked = { code, label: fund.label, nav: last?.nav ?? fund.nav };

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-xl font-medium tracking-tight">{fund.label}</h1>
          <div className="mt-1 flex flex-wrap gap-x-3 text-xs text-muted-foreground">
            {fund.amc && <span>{fund.amc}</span>}
            {fund.category && <span>{fund.category}</span>}
            <span>{ASSET_CLASS[fund.asset_class]?.label ?? fund.asset_class}</span>
            {fund.option && <span>{fund.option}</span>}
          </div>
        </div>
        {last && (
          <div className="num text-right">
            <div className="text-3xl font-medium tracking-tight">{num(last.nav, 4)}</div>
            <div className={cn("text-sm", tone(change))}>
              {change !== null && `${change > 0 ? "+" : ""}${num(change, 4)} (${pct((change / prev.nav) * 100, { signed: true })})`}
              <span className="ml-2 text-xs text-muted-foreground">NAV on {date(last.date)}</span>
            </div>
          </div>
        )}
      </header>

      <PricePanel prices={prices} isPending={false} title="NAV" />

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Returns">
          {returns.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">NAV history is still loading.</p>
          ) : (
            <dl className="num grid grid-cols-3 gap-4 sm:grid-cols-5">
              {returns.map((r) => (
                <div key={r.label}>
                  <dt className="text-xs text-muted-foreground">{r.label}{r.annualised ? " a.a." : ""}</dt>
                  <dd className={cn("mt-0.5 text-[15px] font-medium", tone(r.value))}>{r.value === null ? "–" : pct(r.value, { signed: true })}</dd>
                </div>
              ))}
            </dl>
          )}
          <p className="mt-4 text-[11px] text-muted-foreground">From NAV history. Periods over a year are annualised. Past returns describe what happened, not what will.</p>
        </Panel>

        <Panel title="Your position">
          {lots.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">You don&apos;t hold this fund.</p>
          ) : (
            <table className="num w-full text-[13px]">
              <thead>
                <tr className="text-left text-xs text-muted-foreground">
                  <th className="pb-2 font-normal">Held at</th>
                  <th className="pb-2 text-right font-normal">Units</th>
                  <th className="pb-2 text-right font-normal">Invested</th>
                  <th className="pb-2 text-right font-normal">Value</th>
                  <th className="pb-2 text-right font-normal">Return</th>
                </tr>
              </thead>
              <tbody>
                {lots.map((h) => (
                  <tr key={h.id} className="border-t border-border/70">
                    <td className="py-2"><span className="mr-2 inline-block size-2 rounded-full" style={{ background: brokerColor(h.broker) }} />{h.broker}</td>
                    <td className="py-2 text-right">{num(h.quantity, 3)}</td>
                    <td className="py-2 text-right">{inr(h.invested)}</td>
                    <td className="py-2 text-right">{inr(h.value)}</td>
                    <td className={cn("py-2 text-right", tone(h.pnl))}>{pct(h.pnl_pct, { signed: true })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {lots.some((h) => (h.realized ?? 0) !== 0) && (
            <p className="mt-3 text-xs text-muted-foreground">
              Realised from sales: <span className={tone(lots.reduce((s, h) => s + (h.realized ?? 0), 0))}>{inr(lots.reduce((s, h) => s + (h.realized ?? 0), 0), { signed: true })}</span>
            </p>
          )}
        </Panel>
      </div>

      <Panel
        title="Your entries"
        actions={<Button size="sm" variant="outline" onClick={() => setForm({ open: true, target: { fund: picked } })}><PlusIcon /> Add entry</Button>}
        bodyClassName="p-0"
      >
        {fund.transactions.length === 0 ? (
          <p className="p-8 text-center text-sm text-muted-foreground">No entries yet. Add what you bought to start tracking this fund.</p>
        ) : (
          <table className="num w-full text-[13px]">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="py-2 pl-4 font-normal">Date</th>
                <th className="px-3 py-2 font-normal">Held at</th>
                <th className="px-3 py-2 font-normal">Type</th>
                <th className="px-3 py-2 text-right font-normal">Units</th>
                <th className="px-3 py-2 text-right font-normal">Amount</th>
                <th className="hidden px-3 py-2 text-right font-normal sm:table-cell">Per unit</th>
                <th className="w-10"><span className="sr-only">Edit</span></th>
              </tr>
            </thead>
            <tbody>
              {fund.transactions.map((t) => (
                <tr key={t.id} className="border-b border-border/70 last:border-0">
                  <td className="py-2 pl-4">{t.date ? date(t.date) : <span className="text-muted-foreground">Not set</span>}</td>
                  <td className="px-3 py-2">{t.broker}</td>
                  <td className={cn("px-3 py-2", t.kind === "sell" && "text-loss")}>{t.kind === "buy" ? "Bought" : "Sold"}</td>
                  <td className="px-3 py-2 text-right">{num(t.units, 3)}</td>
                  <td className="px-3 py-2 text-right">{inr(t.amount, { precise: true })}</td>
                  <td className="hidden px-3 py-2 text-right sm:table-cell">{inr(t.amount / t.units, { precise: true })}</td>
                  <td className="pr-2 text-right">
                    <button type="button" onClick={() => setForm({ open: true, target: { fund: picked, entry: t } })} aria-label="Edit entry"
                      className="rounded p-1.5 text-text-tertiary hover:bg-muted hover:text-foreground">
                      <PencilIcon className="size-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      <MfForm open={form.open} onOpenChange={(open) => setForm((f) => ({ ...f, open }))} target={form.target} />
    </div>
  );
}
