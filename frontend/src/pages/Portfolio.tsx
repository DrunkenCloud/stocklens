import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../api";

type Holding = {
  id: string;
  symbol: string;
  quantity: number;
  avg_cost: number;
  buy_date: string | null;
  account: string | null;
  latest_close: number | null;
  cost_basis: number;
  current_value: number | null;
  gain: number | null;
  gain_pct: number | null;
};

type PortfolioData = {
  holdings: Holding[];
  total_cost_basis: number;
  total_current_value: number;
  total_gain: number;
  total_gain_pct: number | null;
};

function fmtRupee(v: number | null): string {
  return v === null ? "N/A" : `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function fmtPct(v: number | null): string {
  return v === null ? "N/A" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

export default function Portfolio() {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [avgCost, setAvgCost] = useState("");
  const [account, setAccount] = useState("");
  const [error, setError] = useState("");

  function refresh() {
    fetch(`${API_URL}/portfolio`)
      .then((res) => {
        if (!res.ok) throw new Error(`portfolio fetch failed: ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch(() => setError("Couldn't reach the backend. Is the API running?"));
  }

  useEffect(refresh, []);

  async function addHolding(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const res = await fetch(`${API_URL}/portfolio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: symbol.toUpperCase(),
        quantity: parseFloat(quantity),
        avg_cost: parseFloat(avgCost),
        account: account || null,
      }),
    });
    if (!res.ok) {
      const body = await res.json();
      setError(body.detail ?? "failed to add holding");
      return;
    }
    setSymbol("");
    setQuantity("");
    setAvgCost("");
    setAccount("");
    refresh();
  }

  async function removeHolding(id: string) {
    await fetch(`${API_URL}/portfolio/${id}`, { method: "DELETE" });
    refresh();
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto" }}>
      <h1>Portfolio</h1>
      <p style={{ fontSize: 12, color: "#666" }}>
        Manually entered holdings. Returns are price-only, not dividend-adjusted. Not investment advice.
      </p>

      <form onSubmit={addHolding} style={{ display: "flex", gap: 8, alignItems: "center", margin: "16px 0", flexWrap: "wrap" }}>
        <input placeholder="Symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)} style={{ width: 100 }} required />
        <input placeholder="Quantity" type="number" step="any" value={quantity} onChange={(e) => setQuantity(e.target.value)} style={{ width: 90 }} required />
        <input placeholder="Avg cost/share" type="number" step="any" value={avgCost} onChange={(e) => setAvgCost(e.target.value)} style={{ width: 110 }} required />
        <input placeholder="Account (optional)" value={account} onChange={(e) => setAccount(e.target.value)} style={{ width: 140 }} />
        <button type="submit">Add holding</button>
      </form>
      {error && <p style={{ color: "#b00" }}>{error}</p>}

      {data && (
        <>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #ddd" }}>
                <th style={{ textAlign: "left", padding: 6 }}>Symbol</th>
                <th style={{ textAlign: "right", padding: 6 }}>Qty</th>
                <th style={{ textAlign: "right", padding: 6 }}>Avg cost</th>
                <th style={{ textAlign: "right", padding: 6 }}>Latest close</th>
                <th style={{ textAlign: "right", padding: 6 }}>Value</th>
                <th style={{ textAlign: "right", padding: 6 }}>Gain</th>
                <th style={{ textAlign: "left", padding: 6 }}>Account</th>
                <th style={{ padding: 6 }} />
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((h) => (
                <tr key={h.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 6 }}>
                    <Link to={`/stock/${h.symbol}`}>{h.symbol}</Link>
                  </td>
                  <td style={{ textAlign: "right", padding: 6 }}>{h.quantity}</td>
                  <td style={{ textAlign: "right", padding: 6 }}>{fmtRupee(h.avg_cost)}</td>
                  <td style={{ textAlign: "right", padding: 6 }}>{fmtRupee(h.latest_close)}</td>
                  <td style={{ textAlign: "right", padding: 6 }}>{fmtRupee(h.current_value)}</td>
                  <td style={{ textAlign: "right", padding: 6, color: (h.gain ?? 0) >= 0 ? "#080" : "#b00" }}>
                    {fmtRupee(h.gain)} ({fmtPct(h.gain_pct)})
                  </td>
                  <td style={{ padding: 6 }}>{h.account ?? ""}</td>
                  <td style={{ padding: 6 }}>
                    <button onClick={() => removeHolding(h.id)}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.holdings.length === 0 && <p>No holdings yet. Add one above.</p>}

          {data.holdings.length > 0 && (
            <p style={{ marginTop: 16, fontWeight: "bold" }}>
              Total: {fmtRupee(data.total_current_value)} ({fmtPct(data.total_gain_pct)}, {fmtRupee(data.total_gain)})
            </p>
          )}
        </>
      )}
    </main>
  );
}
