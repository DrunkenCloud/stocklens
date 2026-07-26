import { Routes, Route, Link } from "react-router-dom";
import Screener from "./pages/Screener";
import Portfolio from "./pages/Portfolio";
import StockDetail from "./pages/StockDetail";
import Admin from "./pages/Admin";
import { API_URL } from "./api";

async function refreshBreezeSession() {
  const res = await fetch(`${API_URL}/breeze/login-url`);
  const { url } = await res.json();
  window.location.href = url;
}

export default function App() {
  return (
    <>
      <nav style={{ padding: "12px 24px", borderBottom: "1px solid #eee", fontFamily: "system-ui, sans-serif" }}>
        <Link to="/" style={{ marginRight: 16 }}>Screener</Link>
        <Link to="/portfolio" style={{ marginRight: 16 }}>Portfolio</Link>
        <Link to="/admin" style={{ marginRight: 16 }}>Admin</Link>
        <button
          onClick={refreshBreezeSession}
          style={{ background: "none", border: "none", color: "#2563eb", textDecoration: "underline", cursor: "pointer", padding: 0, font: "inherit" }}
        >
          Refresh Breeze session
        </button>
      </nav>
      <Routes>
        <Route path="/" element={<Screener />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/stock/:symbol" element={<StockDetail />} />
      </Routes>
    </>
  );
}
