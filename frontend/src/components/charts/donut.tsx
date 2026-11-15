"use client";

import { useRef, useState } from "react";

import { inrCompact } from "@/lib/format";

export interface DonutSlice {
  key: string;
  label: string;
  value: number;
  color: string;
}

export function Donut({
  slices, size = 168, thickness = 22, active, onActiveChange, onSelect, center, format = inrCompact,
}: {
  slices: DonutSlice[];
  size?: number;
  thickness?: number;
  active?: string | null;
  onActiveChange?: (key: string | null) => void;
  onSelect?: (key: string) => void;
  center?: React.ReactNode;
  format?: (v: number) => string;
}) {
  const box = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{ key: string; x: number; y: number } | null>(null);
  const total = slices.reduce((s, x) => s + x.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const gap = slices.length > 1 ? 2 : 0;
  const focused = hover?.key ?? active ?? null;
  const tip = hover ? slices.find((s) => s.key === hover.key) : null;
  let offset = 0;

  const point = (e: React.PointerEvent, key: string) => {
    const r = box.current?.getBoundingClientRect();
    if (!r) return;
    setHover({ key, x: e.clientX - r.left, y: e.clientY - r.top });
    onActiveChange?.(key);
  };
  const leave = () => {
    setHover(null);
    onActiveChange?.(null);
  };

  return (
    <div ref={box} className="relative shrink-0" style={{ width: size, height: size }} onPointerLeave={leave}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" role="img"
        aria-label={slices.map((s) => `${s.label} ${((s.value / total) * 100).toFixed(1)}%`).join(", ")}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--muted)" strokeWidth={thickness} />
        {total > 0 &&
          slices.map((s) => {
            const length = (s.value / total) * circumference;
            const dash = Math.max(0, length - gap);
            const el = (
              <circle
                key={s.key}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={s.color}
                strokeWidth={focused === s.key ? thickness + 4 : thickness}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
                opacity={focused && focused !== s.key ? 0.35 : 1}
                onPointerMove={(e) => point(e, s.key)}
                onPointerDown={(e) => point(e, s.key)}
                onClick={onSelect ? () => onSelect(s.key) : undefined}
                className="cursor-pointer transition-[opacity,stroke-width] duration-150"
              />
            );
            offset += length;
            return el;
          })}
      </svg>
      {center && <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">{center}</div>}
      {tip && hover && (
        <div
          role="tooltip"
          className="num pointer-events-none absolute z-10 w-max max-w-56 rounded-md border border-border bg-popover px-2.5 py-1.5 text-xs text-popover-foreground shadow-sm"
          style={{ left: hover.x, top: hover.y, transform: `translate(${hover.x > size / 2 ? "-100%" : "0"}, -120%)` }}
        >
          <div className="flex items-center gap-1.5 font-medium">
            <span className="size-2 shrink-0 rounded-sm" style={{ background: tip.color }} />
            <span className="truncate">{tip.label}</span>
          </div>
          <div className="mt-0.5 text-muted-foreground">
            {format(tip.value)} <span className="ml-1">{((tip.value / total) * 100).toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
