"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Row = {
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
};

const SORT_COLUMNS: { key: string; label: string }[] = [
  { key: "market_cap", label: "Market cap" },
  { key: "pe", label: "P/E" },
  { key: "pb", label: "P/B" },
  { key: "roe", label: "ROE" },
  { key: "debt_to_equity", label: "D/E" },
  { key: "dividend_yield", label: "Div yield" },
  { key: "rev_cagr_3y", label: "Rev CAGR (3y)" },
];

function fmt(v: number | null, suffix = ""): string {
  return v === null ? "N/A" : `${v.toFixed(2)}${suffix}`;
}

export default function Screener() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [peMax, setPeMax] = useState("");
  const [roeMin, setRoeMin] = useState("");
  const [sector, setSector] = useState("");
  const [sortBy, setSortBy] = useState("market_cap");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    const params = new URLSearchParams({ sort_by: sortBy, order, limit: "100" });
    if (peMax) params.set("pe_max", peMax);
    if (roeMin) params.set("roe_min", roeMin);
    if (sector) params.set("sector", sector);

    setLoading(true);
    setError("");
    fetch(`${API_URL}/screen?${params}`)
      .then((res) => {
        if (!res.ok) throw new Error(`screen fetch failed: ${res.status}`);
        return res.json();
      })
      .then(setRows)
      .catch(() => setError("Couldn't reach the backend. Is the API running?"))
      .finally(() => setLoading(false));
  }, [peMax, roeMin, sector, sortBy, order]);

  function toggleSort(col: string) {
    if (sortBy === col) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setOrder("desc");
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 1000, margin: "0 auto" }}>
      <h1>StockLens Screener</h1>
      <p style={{ fontSize: 12, color: "#666" }}>Descriptive data, not investment advice.</p>

      <div style={{ display: "flex", gap: 16, margin: "16px 0", flexWrap: "wrap" }}>
        <label>
          P/E max{" "}
          <input value={peMax} onChange={(e) => setPeMax(e.target.value)} type="number" style={{ width: 70 }} />
        </label>
        <label>
          ROE min %{" "}
          <input value={roeMin} onChange={(e) => setRoeMin(e.target.value)} type="number" style={{ width: 70 }} />
        </label>
        <label>
          Sector{" "}
          <input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="e.g. IT" style={{ width: 120 }} />
        </label>
      </div>

      {error && <p style={{ color: "#b00" }}>{error}</p>}
      {loading ? (
        <p>Loading...</p>
      ) : error ? null : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #ddd" }}>
              <th style={{ textAlign: "left", padding: 6 }}>Symbol</th>
              {SORT_COLUMNS.map((c) => (
                <th
                  key={c.key}
                  onClick={() => toggleSort(c.key)}
                  style={{ textAlign: "right", padding: 6, cursor: "pointer", userSelect: "none" }}
                >
                  {c.label}
                  {sortBy === c.key ? (order === "asc" ? " ^" : " v") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.symbol} style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: 6 }}>
                  <a href={`/stock/${r.symbol}`}>{r.symbol}</a>
                  <div style={{ fontSize: 11, color: "#666" }}>{r.name}</div>
                </td>
                <td style={{ textAlign: "right", padding: 6 }}>
                  {r.market_cap ? `₹${(r.market_cap / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr` : "N/A"}
                </td>
                <td style={{ textAlign: "right", padding: 6 }}>{fmt(r.pe)}</td>
                <td style={{ textAlign: "right", padding: 6 }}>{fmt(r.pb)}</td>
                <td style={{ textAlign: "right", padding: 6 }}>{fmt(r.roe, "%")}</td>
                <td style={{ textAlign: "right", padding: 6 }}>{fmt(r.debt_to_equity)}</td>
                <td style={{ textAlign: "right", padding: 6 }}>{fmt(r.dividend_yield, "%")}</td>
                <td style={{ textAlign: "right", padding: 6 }}>{fmt(r.rev_cagr_3y, "%")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && !error && rows.length === 0 && <p>No companies match these filters.</p>}
    </main>
  );
}
