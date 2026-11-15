"use client";

import { useState } from "react";

import { Donut, type DonutSlice } from "@/components/charts/donut";
import { Panel, Segmented } from "@/components/panel";
import { ASSET_CLASS, CHART_COLORS, brokerColor, inrCompact, pct } from "@/lib/format";
import type { Portfolio } from "@/lib/types";
import { cn } from "@/lib/utils";


function sectorSlices(p: Portfolio): DonutSlice[] {
  const top = p.by_sector.slice(0, 9);
  const rest = p.by_sector.slice(9).reduce((s, x) => s + x.value, 0);
  const slices = top.map((s, i) => ({ key: s.sector, label: s.sector, value: s.value, color: CHART_COLORS[i] }));
  return rest > 0 ? [...slices, { key: "rest", label: "Others", value: rest, color: CHART_COLORS[10] }] : slices;
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
  const slices = by === "asset" ? assetSlices(portfolio) : by === "broker" ? brokerSlices(portfolio) : sectorSlices(portfolio);
  const total = slices.reduce((s, x) => s + x.value, 0);
  const focused = slices.find((s) => s.key === active);

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
              <li
                key={s.key}
                onMouseEnter={() => setActive(s.key)}
                onMouseLeave={() => setActive(null)}
                className={cn("flex items-center gap-2 rounded px-1.5 py-1", active === s.key && "bg-muted")}
              >
                <span className="size-2.5 shrink-0 rounded-sm" style={{ background: s.color }} aria-hidden />
                <span className="min-w-0 flex-1 truncate">{s.label}</span>
                <span className="text-muted-foreground">{inrCompact(s.value)}</span>
                <span className="w-12 text-right">{pct((s.value / total) * 100, { digits: 1 })}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}
