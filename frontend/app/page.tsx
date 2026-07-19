// ponytail: hardcoded list stands in for the screener (M4). Replace with a
// GET /screen-backed table once that endpoint exists.
const SAMPLE_SYMBOLS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC"];

export default function Home() {
  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1>StockLens</h1>
      <p>Screener isn&apos;t built yet. Sample stock pages:</p>
      <ul>
        {SAMPLE_SYMBOLS.map((s) => (
          <li key={s}>
            <a href={`/stock/${s}`}>{s}</a>
          </li>
        ))}
      </ul>
    </main>
  );
}
