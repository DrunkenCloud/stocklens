"use client";

import { useState } from "react";

import { ChevronRightIcon } from "lucide-react";

import { Donut, type DonutSlice } from "@/components/charts/donut";
import { TagSheet, type TagSelection } from "@/components/exposure/tag-sheet";
import { useScope } from "@/hooks/use-scope";
import { Panel, Segmented } from "@/components/panel";
import { ASSET_CLASS, CHART_COLORS, brokerColor, inrCompact, pct } from "@/lib/format";
import type { Portfolio } from "@/lib/types";
import { cn } from "@/lib/utils";


function sectorSlices(p: Portfolio): DonutSlice[] {
  return p.by_sector.map((s, i) => ({ key: s.sector, label: s.sector, value: s.value, color: CHART_COLORS[i % CHART_COLORS.length] }));
}

function brokerSlices(p: Portfolio): DonutSlice[] {
  return p.by_broker.filter((b) => b.value > 0).map((b) => ({ key: b.broker, label: b.broker, value: b.value, color: brokerColor(b.broker) }));
}

function assetSlices(p: Portfolio): DonutSlice[] {
  return p.by_asset_class.map((a) => ({
    key: a.asset_class,
    label: ASSET_CLASS[a.asset_class]?.label ?? a.asset_class,
    value: a.value,
    color: ASSET_CLASS[a.asset_class]?.color ?? "#a0a0a0",
  }));
}

export function Allocation({ portfolio }: { portfolio: Portfolio }) {
  const [by, setBy] = useState<"asset" | "broker" | "sector">("asset");
  const [active, setActive] = useState<string | null>(null);
  const [sel, setSel] = useState<TagSelection | null>(null);
  const [scope] = useScope();
  const slices = by === "asset" ? assetSlices(portfolio) : by === "broker" ? brokerSlices(portfolio) : sectorSlices(portfolio);
  const total = slices.reduce((s, x) => s + x.value, 0);
  const focused = slices.find((s) => s.key === active);
  const select = by === "broker" ? undefined : (key: string) => {
    const s = slices.find((x) => x.key === key);
    if (!s) return;
    setSel({
      key: `${by}:${key}`, tag: key, label: s.label, color: s.color, base: total,
      baseLabel: by === "sector" ? "your equity" : "everything you hold",
      sector: by === "sector" ? portfolio.by_sector.find((x) => x.sector === key) : undefined,
    });
  };

  return (
    <Panel
      className="h-full"
      bodyClassName="flex items-center"
      title="Allocation"
      actions={
        <Segmented label="Group by" value={by} onChange={(v) => { setBy(v); setActive(null); }}
          options={[{ value: "asset", label: "Asset" }, { value: "broker", label: "Broker" }, { value: "sector", label: "Sector" }]} />
      }
    >
      {slices.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">Allocation appears once prices load.</p>
      ) : (
        <div className="flex w-full flex-col items-center gap-5 sm:flex-row lg:flex-col">
          <Donut
            slices={slices}
            active={active}
            onActiveChange={setActive}
            onSelect={select}
            center={
              <div className="num">
                <div className="text-[11px] text-muted-foreground">{focused ? focused.label : "Total"}</div>
                <div className="text-sm font-medium">{inrCompact(focused ? focused.value : total)}</div>
                {focused && <div className="text-[11px] text-muted-foreground">{pct((focused.value / total) * 100, { digits: 1 })}</div>}
              </div>
            }
          />
          <ul className="num w-full min-w-0 flex-1 space-y-1 text-[13px]">
            {slices.map((s) => (
              <li key={s.key} onMouseEnter={() => setActive(s.key)} onMouseLeave={() => setActive(null)}>
                <button type="button" disabled={!select} onClick={() => select?.(s.key)}
                  className={cn("flex w-full items-center gap-2 rounded px-1.5 py-1 text-left enabled:hover:bg-muted disabled:cursor-default", active === s.key && "bg-muted")}>
                  <span className="size-2.5 shrink-0 rounded-sm" style={{ background: s.color }} aria-hidden />
                  <span className="min-w-0 flex-1 truncate">{s.label}</span>
                  <span className="text-muted-foreground">{inrCompact(s.value)}</span>
                  <span className="w-12 text-right">{pct((s.value / total) * 100, { digits: 1 })}</span>
                  {select && <ChevronRightIcon className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <TagSheet scope={scope} sel={sel} onClose={() => setSel(null)} />
    </Panel>
  );
}
