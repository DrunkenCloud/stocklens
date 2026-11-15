"use client";

export interface DonutSlice {
  key: string;
  label: string;
  value: number;
  color: string;
}

export function Donut({
  slices, size = 168, thickness = 22, active, onActiveChange, center,
}: {
  slices: DonutSlice[];
  size?: number;
  thickness?: number;
  active?: string | null;
  onActiveChange?: (key: string | null) => void;
  center?: React.ReactNode;
}) {
  const total = slices.reduce((s, x) => s + x.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const gap = slices.length > 1 ? 2 : 0;
  let offset = 0;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
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
                strokeWidth={active === s.key ? thickness + 4 : thickness}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
                opacity={active && active !== s.key ? 0.35 : 1}
                onMouseEnter={() => onActiveChange?.(s.key)}
                onMouseLeave={() => onActiveChange?.(null)}
                className="transition-[opacity,stroke-width] duration-150"
              />
            );
            offset += length;
            return el;
          })}
      </svg>
      {center && <div className="absolute inset-0 grid place-items-center text-center">{center}</div>}
    </div>
  );
}
