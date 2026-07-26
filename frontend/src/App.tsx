import { Routes, Route, Link } from "react-router-dom";
import Screener from "./pages/Screener";
import Portfolio from "./pages/Portfolio";
import StockDetail from "./pages/StockDetail";

export default function App() {
  return (
    <>
      <nav style={{ padding: "12px 24px", borderBottom: "1px solid #eee", fontFamily: "system-ui, sans-serif" }}>
        <Link to="/" style={{ marginRight: 16 }}>Screener</Link>
        <Link to="/portfolio">Portfolio</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Screener />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/stock/:symbol" element={<StockDetail />} />
      </Routes>
    </>
  );
}
