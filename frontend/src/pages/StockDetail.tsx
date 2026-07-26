import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API_URL } from "../api";

type PricePoint = { date: string; close: number };

type Fundamentals = {
  snapshot_date: string;
  pe: number | null;
  pb: number | null;
  roe: number | null;
  op_margin: number | null;
  rev_growth_1y: number | null;
  rev_cagr_3y: number | null;
  debt_to_equity: number | null;
  dividend_yield: number | null;
  market_cap: number | null;
};

type Stock = {
  symbol: string;
  name: string;
  sector: string | null;
  fundamentals: Fundamentals | null;
};

type Returns = {
  date_start: string;
  total_return_pct: number;
  cagr_pct: number | null;
  max_drawdown_pct: number;
  best_year: { year: number; return_pct: number };
  worst_year: { year: number; return_pct: number };
  amount_invested: number;
  value_now: number;
};

function PriceChart({ points }: { points: PricePoint[] }) {
  if (points.length < 2) return <p>Not enough data to chart.</p>;

  const width = 800;
  const height = 300;
  const padding = 20;
  const closes = points.map((p) => p.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;

  const coords = points.map((p, i) => {
    const x = padding + (i / (points.length - 1)) * (width - 2 * padding);
    const y = height - padding - ((p.close - min) / range) * (height - 2 * padding);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: "100%", height: "auto", background: "#fafafa", border: "1px solid #ddd" }}
    >
      <polyline points={coords.join(" ")} fill="none" stroke="#2563eb" strokeWidth={1.5} />
    </svg>
  );
}

function fmt(v: number | null, suffix = ""): string {
  return v === null ? "N/A" : `${v.toFixed(2)}${suffix}`;
}

function FundamentalsCard({ stock }: { stock: Stock }) {
  const f = stock.fundamentals;
  if (!f) return <p>No fundamentals data yet. Run pipeline/jobs/fetch_fundamentals.py.</p>;

  return (
    <section style={{ marginTop: 24 }}>
      <h2>Fundamentals (as of {f.snapshot_date})</h2>
      <ul>
        <li>P/E: {fmt(f.pe)}</li>
        <li>P/B: {fmt(f.pb)}</li>
        <li>ROE: {fmt(f.roe, "%")}</li>
        <li>Operating margin: {fmt(f.op_margin, "%")}</li>
        <li>Revenue growth (1yr): {fmt(f.rev_growth_1y, "%")}</li>
        <li>Revenue CAGR (3yr): {fmt(f.rev_cagr_3y, "%")}</li>
        <li>Debt-to-equity: {fmt(f.debt_to_equity)}</li>
        <li>Dividend yield: {fmt(f.dividend_yield, "%")}</li>
        <li>Market cap: {f.market_cap ? `₹${(f.market_cap / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr` : "N/A"}</li>
      </ul>
      <p style={{ fontSize: 12, color: "#666" }}>Free-source data, may be incomplete. Descriptive only, not investment advice.</p>
    </section>
  );
}

function yearsAgo(n: number): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - n);
  return d.toISOString().slice(0, 10);
}

export default function StockDetail() {
  const { symbol = "" } = useParams<{ symbol: string }>();
  const [stock, setStock] = useState<Stock | null | undefined>(undefined);
  const [prices, setPrices] = useState<PricePoint[] | null | undefined>(undefined);
  const [returns, setReturns] = useState<Returns | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!symbol) return;
    setStock(undefined);
    setPrices(undefined);
    setReturns(null);
    setError("");

    fetch(`${API_URL}/stocks/${symbol}`)
      .then((res) => {
        if (res.status === 404) return null;
        if (!res.ok) throw new Error(`stock fetch failed: ${res.status}`);
        return res.json();
      })
      .then(setStock)
      .catch(() => setError("Couldn't reach the backend. Is the API running?"));

    fetch(`${API_URL}/prices/${symbol}`)
      .then((res) => {
        if (res.status === 404) return null;
        if (!res.ok) throw new Error(`prices fetch failed: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setPrices(data);
        if (data) {
          fetch(`${API_URL}/prices/${symbol}/returns?from=${yearsAgo(5)}&amount=100000`)
            .then((res) => (res.ok ? res.json() : null))
            .then(setReturns);
        }
      })
      .catch(() => setError("Couldn't reach the backend. Is the API running?"));
  }, [symbol]);

  if (error) {
    return (
      <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
        <p style={{ color: "#b00" }}>{error}</p>
      </main>
    );
  }

  if (stock === undefined || prices === undefined) {
    return (
      <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
        <p>Loading...</p>
      </main>
    );
  }

  if (!stock) {
    return (
      <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
        <h1>{symbol}</h1>
        <p>Unknown symbol.</p>
      </main>
    );
  }

  if (!prices) {
    return (
      <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
        <h1>{stock.name} ({stock.symbol})</h1>
        {stock.sector && <p>{stock.sector}</p>}
        <p>No price data yet. Run the pipeline (see pipeline/README.md) once Breeze credentials are set up.</p>
        <FundamentalsCard stock={stock} />
      </main>
    );
  }

  const latestPriceDate = prices[prices.length - 1].date;

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto" }}>
      <h1>{stock.name} ({stock.symbol})</h1>
      {stock.sector && <p style={{ color: "#666", marginTop: -8 }}>{stock.sector}</p>}
      <p style={{ fontSize: 12, color: "#666" }}>Prices as of {latestPriceDate}</p>
      <PriceChart points={prices.map((p) => ({ date: p.date, close: p.close }))} />
      <FundamentalsCard stock={stock} />

      {returns && (
        <section style={{ marginTop: 24 }}>
          <h2>Returns since {returns.date_start}</h2>
          <ul>
            <li>Total return: {returns.total_return_pct.toFixed(2)}%</li>
            <li>CAGR: {returns.cagr_pct !== null ? `${returns.cagr_pct.toFixed(2)}%` : "N/A (period < 1yr)"}</li>
            <li>Max drawdown: {returns.max_drawdown_pct.toFixed(2)}%</li>
            <li>
              Best year: {returns.best_year.year} ({returns.best_year.return_pct.toFixed(2)}%)
            </li>
            <li>
              Worst year: {returns.worst_year.year} ({returns.worst_year.return_pct.toFixed(2)}%)
            </li>
            <li>
              ₹{returns.amount_invested.toLocaleString("en-IN")} invested on {returns.date_start} would be worth ₹
              {returns.value_now.toLocaleString("en-IN", { maximumFractionDigits: 0 })} now
            </li>
          </ul>
          <p style={{ fontSize: 12, color: "#666" }}>
            Price return only, not dividend-adjusted. Descriptive historical data, not investment advice.
          </p>
        </section>
      )}
    </main>
  );
}
