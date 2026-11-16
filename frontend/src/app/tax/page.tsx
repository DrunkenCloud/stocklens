"use client";

import Link from "next/link";

import { Panel } from "@/components/panel";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { date, inr, qty, tone } from "@/lib/format";
import { holdingHref, shortFundName } from "@/lib/holding";
import { useTax } from "@/lib/queries";
import type { GainSplit, TaxClass, TaxLot } from "@/lib/types";
import { cn } from "@/lib/utils";

const CLASSES: Record<TaxClass, { label: string; rule: string }> = {
  equity: { label: "Equity", rule: "Stocks, equity funds and ETFs. Long-term after 12 months; short-term 20%, long-term 12.5% above ₹1.25 lakh a year." },
  listed_other: { label: "Gold and silver ETFs", rule: "Long-term after 12 months; short-term at your slab rate, long-term 12.5%." },
  unlisted_other: { label: "Fund of funds and other funds", rule: "Long-term after 24 months; short-term at your slab rate, long-term 12.5%." },
  debt: { label: "Debt funds", rule: "Units bought from April 2023 are short-term at your slab rate however long you hold them." },
};

function name(l: TaxLot) {
  return l.kind === "mf" ? shortFundName(l.name) : l.symbol;
}

function status(l: TaxLot) {
  if (l.term === "unknown") return "Purchase date unknown";
  if (l.term === "always_short") return "Always short-term";
  if (l.term === "long") return "Long-term";
  return `Short-term until ${date(l.long_term_on)}`;
}

function Upcoming({ lots }: { lots: TaxLot[] }) {
  if (lots.length === 0) return <p className="text-sm text-muted-foreground">Nothing turns long-term in the next 90 days.</p>;
  return (
    <ul className="divide-y divide-border">
      {lots.map((l, i) => (
        <li key={i} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 py-2 text-sm first:pt-0 last:pb-0">
          <div className="min-w-0">
            <Link href={holdingHref(l)} className="font-medium hover:underline">{name(l)}</Link>
            <span className="ml-1.5 text-xs text-muted-foreground">{l.broker} · {qty(l.units)} bought {date(l.date)}</span>
          </div>
          <div className="flex items-baseline gap-4">
            <span className={cn("num", tone(l.gain))}>{inr(l.gain, { signed: true })}</span>
            <span className="num w-40 text-right">
              {date(l.long_term_on)} <span className="text-xs text-muted-foreground">in {l.days_left} d</span>
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

function Split({ title, split }: { title: string; split: GainSplit }) {
  const rows = (Object.keys(CLASSES) as TaxClass[]).filter((c) => split[c]);
  return (
    <div>
      <div className="mb-1 text-xs text-muted-foreground">{title}</div>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">None</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-muted-foreground">
              <th className="py-1 text-left font-normal" />
              <th className="py-1 text-right font-normal">Short-term</th>
              <th className="py-1 text-right font-normal">Long-term</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => {
              const s = split[c]!;
              return (
                <tr key={c} className="border-t border-border">
                  <td className="py-1.5">
                    {CLASSES[c].label}
                    {Math.abs(s.unknown) >= 1 && <div className="text-xs text-muted-foreground">plus <span className={cn("num", tone(s.unknown))}>{inr(s.unknown, { signed: true })}</span> with no purchase date</div>}
                  </td>
                  <td className={cn("num py-1.5 text-right", tone(s.short))}>{inr(s.short, { signed: true })}</td>
                  <td className={cn("num py-1.5 text-right", tone(s.long))}>{inr(s.long, { signed: true })}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

function Lots({ lots }: { lots: TaxLot[] }) {
  return (
    <>
      <table className="hidden w-full text-sm lg:table">
        <thead>
          <tr className="border-b border-border text-xs text-muted-foreground">
            <th className="px-4 py-2 text-left font-normal">Holding</th>
            <th className="px-2 py-2 text-left font-normal">Broker</th>
            <th className="px-2 py-2 text-left font-normal">Bought</th>
            <th className="px-2 py-2 text-right font-normal">Units</th>
            <th className="px-2 py-2 text-right font-normal">Cost</th>
            <th className="px-2 py-2 text-right font-normal">Value</th>
            <th className="px-2 py-2 text-right font-normal">Gain</th>
            <th className="px-4 py-2 text-left font-normal">Status</th>
          </tr>
        </thead>
        <tbody>
          {lots.map((l, i) => (
            <tr key={i} className="border-b border-border last:border-0">
              <td className="px-4 py-2"><Link href={holdingHref(l)} className="hover:underline">{name(l)}</Link></td>
              <td className="px-2 py-2 text-muted-foreground">{l.broker}</td>
              <td className="num px-2 py-2">{date(l.date)}</td>
              <td className="num px-2 py-2 text-right">{qty(l.units)}</td>
              <td className="num px-2 py-2 text-right">{inr(l.cost)}</td>
              <td className="num px-2 py-2 text-right">{inr(l.value)}</td>
              <td className={cn("num px-2 py-2 text-right", tone(l.gain))}>{inr(l.gain, { signed: true })}</td>
              <td className={cn("px-4 py-2", l.term === "long" ? "" : "text-muted-foreground")}>{status(l)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <ul className="divide-y divide-border lg:hidden">
        {lots.map((l, i) => (
          <li key={i} className="px-4 py-2.5 text-sm">
            <div className="flex justify-between gap-2">
              <Link href={holdingHref(l)} className="truncate font-medium hover:underline">{name(l)}</Link>
              <span className={cn("num shrink-0", tone(l.gain))}>{inr(l.gain, { signed: true })}</span>
            </div>
            <div className="mt-0.5 flex justify-between gap-2 text-xs text-muted-foreground">
              <span>{l.broker} · {qty(l.units)} {l.date ? `bought ${date(l.date)}` : "units"}</span>
              <span className="shrink-0">{status(l)}</span>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}

export default function TaxPage() {
  const { data, isPending, isError, error, refetch } = useTax();

  let body: React.ReactNode;
  if (isPending) {
    body = (
      <div className="space-y-4" aria-busy>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  } else if (isError) {
    body = (
      <div className="py-16">
        <p className="text-loss">{error.message}</p>
        <Button variant="outline" className="mt-4" onClick={() => refetch()}>Try again</Button>
      </div>
    );
  } else {
    const ex = data.exemption;
    const usedPct = Math.min(100, (ex.used / ex.limit) * 100);
    const classes = Array.from(new Set(data.lots.map((l) => l.tax_class)));
    body = (
      <div className="space-y-4">
        <Panel title="Turning long-term in the next 90 days">
          <Upcoming lots={data.upcoming} />
        </Panel>
        <Panel title={`This financial year (${date(data.fy.start)} – ${date(data.fy.end)})`}>
          <div className="grid gap-6 lg:grid-cols-3">
            <Split title="Booked by selling" split={data.realised} />
            <Split title="On paper, if sold today" split={data.unrealised} />
            <div>
              <div className="mb-1 text-xs text-muted-foreground">Equity long-term exemption</div>
              <div className="num text-lg font-medium">{inr(ex.remaining)} <span className="text-sm font-normal text-muted-foreground">left of {inr(ex.limit)}</span></div>
              <div className="mt-2 h-1.5 rounded-full bg-muted" role="img" aria-label={`${inr(ex.used)} of ${inr(ex.limit)} used`}>
                <div className="h-full rounded-full bg-foreground/60" style={{ width: `${usedPct}%` }} />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Long-term equity gains booked this year: {inr(ex.used)}. Gains up to {inr(ex.limit)} a year are not taxed.</p>
            </div>
          </div>
        </Panel>
        <Panel title={`Every lot (${data.lots.length})`} bodyClassName="p-0">
          <Lots lots={data.lots} />
        </Panel>
        <div className="space-y-1 text-xs text-muted-foreground">
          <p>Lots are matched first-in, first-out per holding and broker, as the tax rules require; holding pages show average cost instead.</p>
          {classes.map((c) => <p key={c}><span className="text-foreground">{CLASSES[c].label}:</span> {CLASSES[c].rule}</p>)}
          <p>Rules as in force since 23 July 2024. Surcharge, cess and grandfathering of pre-2018 gains are not shown.</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="mb-4">
        <h1 className="text-lg font-medium">Tax</h1>
      </div>
      {body}
    </>
  );
}
