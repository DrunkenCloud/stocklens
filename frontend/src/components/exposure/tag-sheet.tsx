"use client";

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { inr, inrCompact, pct } from "@/lib/format";
import { shortFundName } from "@/lib/holding";
import { useExposureBreakdown } from "@/lib/queries";
import { describeTag } from "@/lib/tags";
import type { ExposureBreakdown, Scope, SectorGroup } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface TagSelection {
  key: string;
  tag: string;
  label: string;
  color: string;
  base: number;
  baseLabel: string;
  sector?: SectorGroup;
}

const KIND = { stock: "Stock", etf: "ETF", mf: "Fund" } as const;
const PAGE = 60;

function Section({ title, children }: { title: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="border-t border-border px-4 py-3">
      <h3 className="mb-2 text-xs font-medium text-muted-foreground">{title}</h3>
      {children}
    </section>
  );
}

function Bar({ share, color }: { share: number; color: string }) {
  return (
    <div className="mt-1 h-1 rounded-full bg-muted">
      <div className="h-full rounded-full" style={{ width: `${Math.max(1, Math.min(100, share))}%`, background: color }} />
    </div>
  );
}

type Item = ExposureBreakdown["items"][number];

function ItemList({ items, share, page, hideTag }: { items: Item[]; share: (v: number) => number; page: number; hideTag?: boolean }) {
  const [limit, setLimit] = useState(page);
  const shown = items.slice(0, limit);
  return (
    <>
      <ul className="num divide-y divide-border/70 text-[13px]">
        {shown.map((i) => {
          const href = i.symbol ? (i.tracked ? `/stock/?s=${encodeURIComponent(i.symbol)}` : i.isin ? `/stock/?isin=${i.isin}` : null) : null;
          const direct = i.direct > 0 && (i.direct >= i.value - 0.5 ? "held directly" : `${inrCompact(i.direct)} held directly`);
          return (
            <li key={i.isin ?? i.name} className="py-1.5">
              <div className="flex items-baseline justify-between gap-3">
                {href ? <Link href={href} className="truncate font-medium hover:text-accent-blue">{i.name}</Link> : <span className="truncate font-medium">{i.name}</span>}
                <span className="shrink-0 whitespace-nowrap">
                  <span className="text-muted-foreground">{inr(i.value)}</span>
                  <span className="ml-2 inline-block w-12 text-right">{pct(share(i.value), { digits: 1 })}</span>
                </span>
              </div>
              {(!hideTag || direct) && (
                <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                  {!hideTag && (
                    <span title={describeTag(i.tag)} className={cn("truncate rounded border border-border px-1", describeTag(i.tag) && "cursor-help")}>{i.tag}</span>
                  )}
                  {direct && <span className="shrink-0">{direct}</span>}
                </div>
              )}
            </li>
          );
        })}
      </ul>
      {items.length > shown.length && (
        <Button variant="ghost" size="sm" className="mt-1 w-full" onClick={() => setLimit(items.length)}>Show all {items.length}</Button>
      )}
    </>
  );
}

function Body({ sel, data }: { sel: TagSelection; data: ExposureBreakdown }) {
  const [industry, setIndustry] = useState<string | null>(null);
  const tags = [...new Set(data.items.map((i) => i.tag))].filter((t) => describeTag(t));
  const share = (v: number) => (data.value ? (v / data.value) * 100 : 0);

  return (
    <>
      {sel.sector && sel.sector.industries.length > 1 && (
        <Section title={<>Industries <span className="font-normal">(tap one to see its companies)</span></>}>
          <ul className="num space-y-1 text-[13px]">
            {sel.sector.industries.map((d) => {
              const on = industry === d.industry;
              const inside = on ? data.items.filter((i) => i.tag === d.industry) : [];
              return (
                <li key={d.industry} className={cn("rounded", on && "bg-muted/50 ring-1 ring-border")}>
                  <button type="button" onClick={() => setIndustry(on ? null : d.industry)} aria-expanded={on}
                    className={cn("w-full rounded px-2 py-1.5 text-left hover:bg-muted", on && "bg-muted")}>
                    <span className="flex items-baseline justify-between gap-3">
                      <span className="flex min-w-0 items-center gap-1 font-medium">
                        {on ? <ChevronDownIcon className="size-3.5 shrink-0 text-muted-foreground" /> : <ChevronRightIcon className="size-3.5 shrink-0 text-muted-foreground" />}
                        <span className="truncate">{d.industry}</span>
                      </span>
                      <span className="shrink-0 whitespace-nowrap">
                        <span className="text-muted-foreground">{inrCompact(d.value)}</span>
                        <span className="ml-2 inline-block w-12 text-right">{pct(share(d.value), { digits: 1 })}</span>
                      </span>
                    </span>
                    {describeTag(d.industry) && <span className="mt-0.5 block pl-[1.125rem] text-xs text-muted-foreground">{describeTag(d.industry)}</span>}
                    <Bar share={share(d.value)} color={sel.color} />
                  </button>
                  {on && (
                    <div className="px-2 pb-1 pl-[1.625rem]">
                      <ItemList items={inside} share={share} page={15} hideTag />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </Section>
      )}

      <Section title={`From your holdings (${data.holdings.length})`}>
        <ul className="num space-y-2 text-[13px]">
          {data.holdings.map((h) => (
            <li key={`${h.kind}|${h.label}`}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="flex min-w-0 items-baseline gap-2">
                  <span className="shrink-0 rounded bg-muted px-1 text-[10px] text-muted-foreground uppercase">{KIND[h.kind]}</span>
                  <span className="truncate">{h.kind === "mf" ? shortFundName(h.label) : h.label}</span>
                </span>
                <span className="shrink-0 whitespace-nowrap">
                  <span className="text-muted-foreground">{inrCompact(h.value)}</span>
                  <span className="ml-2 inline-block w-12 text-right">{pct(share(h.value), { digits: 1 })}</span>
                </span>
              </div>
              <Bar share={share(h.value)} color={sel.color} />
            </li>
          ))}
        </ul>
      </Section>

      {data.items.length > 0 && (
        <Section title={`What's inside (${data.items.length})`}>
          {!sel.sector && tags.length <= 6 && (
            <dl className="mb-2 space-y-1 rounded bg-muted/60 px-2.5 py-2 text-[11px]">
              {tags.map((t) => (
                <div key={t}>
                  <dt className="inline font-medium">{t}: </dt>
                  <dd className="inline text-muted-foreground">{describeTag(t)}</dd>
                </div>
              ))}
            </dl>
          )}
          <ItemList items={data.items} share={share} page={PAGE} />
        </Section>
      )}
    </>
  );
}

export function TagSheet({ scope, sel, onClose }: { scope: Scope; sel: TagSelection | null; onClose: () => void }) {
  const { data, isPending, isError, error } = useExposureBreakdown(scope, sel?.key ?? null);
  const description = sel ? describeTag(sel.tag) : undefined;

  return (
    <Sheet open={!!sel} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="gap-0 overflow-y-auto data-[side=right]:w-full data-[side=right]:sm:max-w-lg">
        {sel && (
          <>
            <SheetHeader className="pr-12">
              <SheetTitle className="flex items-center gap-2">
                <span className="size-3 shrink-0 rounded-sm" style={{ background: sel.color }} aria-hidden />
                {sel.label}
              </SheetTitle>
              <div className="num text-[13px]">
                <span className="font-medium">{inr(data?.value ?? 0)}</span>
                <span className="ml-2 text-muted-foreground">
                  {data && sel.base ? `${pct((data.value / sel.base) * 100, { digits: 1 })} of ${sel.baseLabel}` : ""}
                </span>
              </div>
              {description && <SheetDescription className="text-xs">{description}</SheetDescription>}
            </SheetHeader>
            {isPending ? (
              <div className="space-y-2 border-t border-border p-4"><Skeleton className="h-6" /><Skeleton className="h-6" /><Skeleton className="h-6" /></div>
            ) : isError ? (
              <p className="border-t border-border p-4 text-sm text-loss">{error.message}</p>
            ) : (
              <Body key={sel.key} sel={sel} data={data} />
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
