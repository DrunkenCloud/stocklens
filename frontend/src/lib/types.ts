export type SessionState = "never" | "expired" | "valid";
export type JobStatus = "running" | "done" | "failed" | "skipped";

export interface Status {
  breeze: { state: SessionState; captured_at: string | null };
  last_sync: { id: number; status: JobStatus; started_at: string; finished_at: string | null; summary: string | null } | null;
  running: string[];
  prices_as_of: string | null;
}

export interface Holding {
  id: string;
  symbol: string;
  name: string;
  sector: string | null;
  quantity: number;
  invested: number;
  broker: string;
  source: "manual" | "icici_sync";
  buy_date: string | null;
  note: string | null;
  close: number | null;
  prev_close: number | null;
  price_date: string | null;
  avg_cost: number;
  value: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  day_change: number | null;
  day_change_pct: number | null;
  weight_pct: number | null;
  spark: number[];
}

export interface HistoryPoint {
  date: string;
  value: number;
}

export interface Portfolio {
  holdings: Holding[];
  totals: {
    invested: number;
    priced_invested: number;
    value: number;
    pnl: number | null;
    pnl_pct: number | null;
    day_change: number;
    day_change_pct: number | null;
  };
  by_broker: { broker: string; invested: number; value: number; pnl: number | null; pnl_pct: number | null; count: number }[];
  by_sector: { sector: string; value: number; weight_pct: number }[];
}

export interface HoldingInput {
  symbol?: string;
  isin?: string;
  quantity: number;
  invested: number;
  broker: string;
  buy_date?: string | null;
  note?: string | null;
}

export interface Security {
  isin: string;
  name: string;
  nse_symbol: string | null;
  bse_code: string | null;
  bse_symbol: string | null;
  tracked: boolean;
  exchanges: ("NSE" | "BSE")[];
}

export interface Fundamentals {
  snapshot_date: string;
  pe: number | null;
  pb: number | null;
  roe: number | null;
  op_margin: number | null;
  rev_ttm: number | null;
  rev_growth_1y: number | null;
  rev_cagr_3y: number | null;
  debt_to_equity: number | null;
  dividend_yield: number | null;
  market_cap: number | null;
}

export interface Stock {
  symbol: string;
  name: string;
  sector: string | null;
  is_active: boolean;
  isin: string | null;
  exchanges: string[];
  fundamentals: Fundamentals | null;
  latest_price: { date: string; close: number; prev_close: number | null } | null;
}

export interface PricePoint {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
}

export interface Returns {
  date_start: string;
  date_end: string;
  close_start: number;
  close_end: number;
  total_return_pct: number;
  cagr_pct: number | null;
  max_drawdown_pct: number;
  best_year: { year: number; return_pct: number };
  worst_year: { year: number; return_pct: number };
  amount_invested: number;
  value_now: number;
  is_price_return_only: boolean;
}

export interface ScreenRow {
  symbol: string;
  name: string;
  sector: string | null;
  pe: number | null;
  pb: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  dividend_yield: number | null;
  rev_cagr_3y: number | null;
  market_cap: number | null;
  latest_close: number | null;
}

export interface JobRun {
  id: number;
  job: string;
  args: string;
  trigger: "cron" | "admin" | "auto";
  status: JobStatus;
  started_at: string;
  finished_at: string | null;
  summary: string | null;
  log_tail?: string;
}

export interface Company {
  symbol: string;
  name: string;
  sector: string | null;
  isin: string | null;
  price_date: string | null;
  close: number | null;
}
