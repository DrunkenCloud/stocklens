import { InfoIcon } from "lucide-react";

import { Panel } from "@/components/panel";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { date, inrCompact, num, pct } from "@/lib/format";
import type { Fundamentals as F } from "@/lib/types";

const METRICS: { key: keyof F; label: string; format: (v: number) => string; explain: string }[] = [
  { key: "market_cap", label: "Market cap", format: inrCompact, explain: "Total value of all the company's shares at the current price." },
  { key: "pe", label: "P/E ratio", format: (v) => num(v), explain: "Share price divided by the last 12 months' earnings per share." },
  { key: "pb", label: "P/B ratio", format: (v) => num(v), explain: "Share price divided by book value (assets minus liabilities) per share." },
  { key: "roe", label: "ROE", format: (v) => pct(v), explain: "Yearly profit as a percentage of shareholders' equity." },
  { key: "op_margin", label: "Operating margin", format: (v) => pct(v), explain: "Operating profit as a percentage of revenue." },
  { key: "dividend_yield", label: "Dividend yield", format: (v) => pct(v), explain: "Dividends paid over a year as a percentage of the share price." },
  { key: "debt_to_equity", label: "Debt to equity", format: (v) => num(v), explain: "Total debt divided by shareholders' equity." },
  { key: "rev_ttm", label: "Revenue (12 months)", format: inrCompact, explain: "Revenue over the last four reported quarters." },
  { key: "rev_growth_1y", label: "Revenue growth (1Y)", format: (v) => pct(v, { signed: true }), explain: "Change in revenue compared with a year earlier." },
  { key: "rev_cagr_3y", label: "Revenue CAGR (3Y)", format: (v) => pct(v, { signed: true }), explain: "Average yearly revenue growth over the last three years." },
];

export function Fundamentals({ data }: { data: F | null }) {
  return (
    <Panel title="Fundamentals" actions={data && <span className="text-[11px] text-muted-foreground">Yahoo Finance, {date(data.snapshot_date)}</span>}>
      {!data ? (
        <p className="py-6 text-center text-sm text-muted-foreground">No fundamentals yet. They load in the background after a stock is tracked.</p>
      ) : (
        <dl className="num grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-5">
          {METRICS.map((m) => {
            const v = data[m.key] as number | null;
            return (
              <div key={m.key}>
                <dt className="flex items-center gap-1 text-xs text-muted-foreground">
                  {m.label}
                  <Tooltip>
                    <TooltipTrigger className="text-text-tertiary hover:text-foreground" aria-label={`What is ${m.label}?`}>
                      <InfoIcon className="size-3" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-56">{m.explain}</TooltipContent>
                  </Tooltip>
                </dt>
                <dd className="mt-0.5 text-[15px] font-medium">{v === null ? <span className="text-text-tertiary">N/A</span> : m.format(v)}</dd>
              </div>
            );
          })}
        </dl>
      )}
    </Panel>
  );
}
