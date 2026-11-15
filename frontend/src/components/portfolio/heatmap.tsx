"use client";

import { useState } from "react";

import { Treemap } from "@/components/charts/treemap";
import { Panel, Segmented } from "@/components/panel";
import { inrCompact } from "@/lib/format";
import type { Holding } from "@/lib/types";

export function Heatmap({ holdings }: { holdings: Holding[] }) {
  const [mode, setMode] = useState<"day" | "total">("day");
  const bySymbol = new Map<string, { value: number; invested: number; prev: number; name: string }>();
  for (const h of holdings) {
    if (h.value === null) continue;
    const cur = bySymbol.get(h.symbol) ?? { value: 0, invested: 0, prev: 0, name: h.name };
    cur.value += h.value;
    cur.invested += h.invested;
    cur.prev += h.prev_close !== null ? h.quantity * h.prev_close : h.value;
    bySymbol.set(h.symbol, cur);
  }
  const items = [...bySymbol].map(([symbol, x]) => ({
    key: symbol,
    label: symbol,
    sublabel: inrCompact(x.value),
    value: x.value,
    change: mode === "day" ? (x.prev ? ((x.value - x.prev) / x.prev) * 100 : null) : ((x.value - x.invested) / x.invested) * 100,
    href: `/stock/?s=${encodeURIComponent(symbol)}`,
  }));

  if (items.length === 0) return null;
  return (
    <Panel
      title="Heatmap"
      actions={
        <Segmented label="Colour by" value={mode} onChange={setMode}
          options={[{ value: "day", label: "1D change" }, { value: "total", label: "Total return" }]} />
      }
      bodyClassName="p-2"
    >
      <Treemap items={items} height={Math.min(380, 140 + items.length * 20)} cap={mode === "day" ? 3 : 40} />
      <div className="num flex items-center justify-end gap-2 px-1 pt-2 text-[11px] text-muted-foreground">
        <span>{mode === "day" ? "−3%" : "−40%"}</span>
        <span className="h-2 w-28 rounded-sm bg-gradient-to-r from-loss via-muted to-gain" aria-hidden />
        <span>{mode === "day" ? "+3%" : "+40%"}</span>
        <span className="ml-2">Tile size is current value</span>
      </div>
    </Panel>
  );
}
