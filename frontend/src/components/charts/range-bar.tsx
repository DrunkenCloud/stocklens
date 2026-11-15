import { inr } from "@/lib/format";

export function RangeBar({ label, low, high, current }: { label: string; low: number; high: number; current: number }) {
  const position = high > low ? Math.min(100, Math.max(0, ((current - low) / (high - low)) * 100)) : 50;
  return (
    <div>
      <div className="mb-2 text-xs text-muted-foreground">{label}</div>
      <div className="num flex items-center gap-3 text-sm">
        <div className="w-20 shrink-0">
          <div className="text-[11px] text-muted-foreground">Low</div>
          <div>{inr(low, { precise: true })}</div>
        </div>
        <div className="relative h-1 flex-1 rounded-full bg-gradient-to-r from-loss/70 via-muted-foreground/30 to-gain/70">
          <div
            className="absolute top-1/2 size-0 -translate-x-1/2 border-x-[5px] border-t-[7px] border-x-transparent border-t-foreground"
            style={{ left: `${position}%`, marginTop: "-10px" }}
            aria-label={`Current ${inr(current, { precise: true })}`}
          />
        </div>
        <div className="w-20 shrink-0 text-right">
          <div className="text-[11px] text-muted-foreground">High</div>
          <div>{inr(high, { precise: true })}</div>
        </div>
      </div>
    </div>
  );
}
