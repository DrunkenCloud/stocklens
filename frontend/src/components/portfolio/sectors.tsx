import type { Portfolio } from "@/lib/types";
import { inrCompact, pct } from "@/lib/format";

/** Share of current value by sector. Bars, not a donut: lengths compare more easily than angles. */
export function Sectors({ sectors }: { sectors: Portfolio["by_sector"] }) {
  if (!sectors.length) return null;
  const max = sectors[0].weight_pct;
  return (
    <section aria-labelledby="sectors-heading">
      <h2 id="sectors-heading" className="mb-3 text-base font-semibold">By sector</h2>
      <ul className="space-y-2.5">
        {sectors.map((s) => (
          <li key={s.sector}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="truncate">{s.sector}</span>
              <span className="num shrink-0 text-muted-foreground">
                {pct(s.weight_pct, { digits: 1 })} <span className="text-xs">{inrCompact(s.value)}</span>
              </span>
            </div>
            <div className="mt-1 h-1.5 rounded-full bg-secondary">
              <div className="h-full rounded-full bg-foreground/70" style={{ width: `${(s.weight_pct / max) * 100}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
