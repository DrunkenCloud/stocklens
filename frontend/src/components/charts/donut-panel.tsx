"use client";

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import { useState } from "react";

import { Donut, type DonutSlice } from "@/components/charts/donut";
import { Panel } from "@/components/panel";
import { CHART_COLORS, inrCompact, pct } from "@/lib/format";
import { cn } from "@/lib/utils";

export function topSlices(rows: { key: string; label: string; value: number; color?: string }[], max: number): DonutSlice[] {
  const sorted = [...rows].sort((a, b) => b.value - a.value);
  const top = sorted.slice(0, max).map((r, i) => ({ ...r, color: r.color ?? CHART_COLORS[i % (CHART_COLORS.length - 1)] }));
  const rest = sorted.slice(max).reduce((s, r) => s + r.value, 0);
  return rest > 0 ? [...top, { key: "__rest", label: `${sorted.length - max} others`, value: rest, color: CHART_COLORS[CHART_COLORS.length - 1] }] : top;
}

export type PanelSlice = DonutSlice & { parts?: { label: string; value: number }[] };

export function DonutPanel({ title, slices, actions }: { title: React.ReactNode; slices: PanelSlice[]; actions?: React.ReactNode }) {
  const [active, setActive] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const total = slices.reduce((s, x) => s + x.value, 0);
  const focused = slices.find((s) => s.key === active);

  return (
    <Panel title={title} actions={actions} className="h-full">
      <div className="flex flex-col items-center gap-4">
        <Donut
          slices={slices}
          size={176}
          active={active}
          onActiveChange={setActive}
          center={
            <div className="num px-6">
              <div className="truncate text-[11px] text-muted-foreground">{focused ? focused.label : "Total"}</div>
              <div className="text-sm font-medium">{inrCompact(focused ? focused.value : total)}</div>
              {focused && <div className="text-[11px] text-muted-foreground">{pct((focused.value / total) * 100, { digits: 1 })}</div>}
            </div>
          }
        />
        <ul className="num w-full space-y-0.5 text-[13px]">
          {slices.map((s) => {
            const expandable = (s.parts?.length ?? 0) > 1;
            const expanded = expandable && open === s.key;
            const row = (
              <>
                <span className="size-2.5 shrink-0 rounded-sm" style={{ background: s.color }} aria-hidden />
                <span className="min-w-0 flex-1 truncate">{s.label}</span>
                {expandable && (expanded ? <ChevronDownIcon className="size-3.5 shrink-0 text-muted-foreground" /> : <ChevronRightIcon className="size-3.5 shrink-0 text-muted-foreground" />)}
                <span className="text-muted-foreground">{inrCompact(s.value)}</span>
                <span className="w-12 text-right">{pct((s.value / total) * 100, { digits: 1 })}</span>
              </>
            );
            const rowClass = cn("flex w-full items-center gap-2 rounded px-1.5 py-1 text-left", active === s.key && "bg-muted");
            return (
              <li key={s.key} onMouseEnter={() => setActive(s.key)} onMouseLeave={() => setActive(null)}>
                {expandable ? (
                  <button type="button" className={cn(rowClass, "hover:bg-muted")} aria-expanded={expanded} onClick={() => setOpen(expanded ? null : s.key)}>
                    {row}
                  </button>
                ) : (
                  <div className={rowClass}>{row}</div>
                )}
                {expanded && (
                  <ul className="mb-1 ml-[1.1rem] space-y-0.5 border-l border-border pl-3 text-xs text-muted-foreground">
                    {s.parts!.map((p) => (
                      <li key={p.label} className="flex items-center gap-2 py-0.5">
                        <span className="min-w-0 flex-1 truncate">{p.label}</span>
                        <span>{inrCompact(p.value)}</span>
                        <span className="w-12 text-right text-foreground">{pct((p.value / total) * 100, { digits: 1 })}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </Panel>
  );
}
