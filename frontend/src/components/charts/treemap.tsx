"use client";

import { hierarchy, treemap, treemapSquarify } from "d3-hierarchy";
import Link from "next/link";
import { useMemo } from "react";

import { useSize } from "@/hooks/use-size";
import { pct } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface TreemapItem {
  key: string;
  label: string;
  sublabel: string;
  value: number;
  change: number | null;
  href: string;
}

function tileColor(change: number | null, cap: number) {
  if (change === null) return { background: "var(--muted)", strong: false };
  const t = Math.min(1, Math.abs(change) / cap);
  const base = change >= 0 ? "var(--gain)" : "var(--loss)";
  return { background: `color-mix(in oklab, ${base} ${Math.round(18 + t * 72)}%, var(--surface))`, strong: t > 0.45 };
}

export function Treemap({ items, height, cap }: { items: TreemapItem[]; height: number; cap: number }) {
  const [ref, { width }] = useSize<HTMLDivElement>();

  const tiles = useMemo(() => {
    if (!width || items.length === 0) return [];
    const root = hierarchy<{ children?: TreemapItem[] } & Partial<TreemapItem>>({ children: items })
      .sum((d) => d.value ?? 0)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
    return treemap<typeof root.data>().tile(treemapSquarify).size([width, height]).paddingInner(2).round(true)(root).leaves();
  }, [items, width, height]);

  return (
    <div ref={ref} className="relative w-full overflow-hidden rounded" style={{ height }}>
      {tiles.map((tile) => {
        const item = tile.data as TreemapItem;
        const w = tile.x1 - tile.x0;
        const h = tile.y1 - tile.y0;
        const { background, strong } = tileColor(item.change, cap);
        const big = w > 90 && h > 46;
        const showLabel = w > 22 && h > 13;
        const showChange = w > 32 && h > 26;
        const showSub = w > 96 && h > 64;
        return (
          <Link
            key={item.key}
            href={item.href}
            title={`${item.label}: ${pct(item.change, { signed: true })}`}
            className="num absolute flex flex-col items-center justify-center overflow-hidden rounded-sm px-1 text-center outline-offset-[-2px] hover:brightness-110"
            style={{ left: tile.x0, top: tile.y0, width: w, height: h, background, color: strong ? "#fff" : "var(--foreground)" }}
          >
            {showLabel && <span className={cn("block max-w-full truncate font-medium leading-tight", big ? "text-sm" : "text-[10px]")}>{item.label}</span>}
            {showChange && <span className={cn("block max-w-full truncate leading-tight opacity-90", big ? "text-xs" : "text-[10px]")}>{pct(item.change, { signed: true })}</span>}
            {showSub && <span className="mt-0.5 block max-w-full truncate text-[11px] opacity-75">{item.sublabel}</span>}
          </Link>
        );
      })}
    </div>
  );
}
