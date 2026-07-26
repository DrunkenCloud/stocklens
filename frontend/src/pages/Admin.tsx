import { useEffect, useState } from "react";
import { API_URL } from "../api";

const JOBS: { key: string; label: string }[] = [
  { key: "fetch_prices", label: "Fetch prices (incremental)" },
  { key: "fetch_prices_backfill", label: "Fetch prices (full backfill)" },
  { key: "fetch_fundamentals", label: "Fetch fundamentals" },
  { key: "map_breeze_codes", label: "Map Breeze codes" },
];

type JobStatus = {
  name: string;
  status: "running" | "done" | "failed";
  started_at: string;
  log_tail: string;
};

export default function Admin() {
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [sector, setSector] = useState("");
  const [companyMsg, setCompanyMsg] = useState("");

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [jobError, setJobError] = useState("");

  useEffect(() => {
    if (!activeJobId) return;
    let cancelled = false;

    async function poll() {
      const res = await fetch(`${API_URL}/admin/jobs/${activeJobId}`);
      if (!res.ok || cancelled) return;
      const data: JobStatus = await res.json();
      if (cancelled) return;
      setJobStatus(data);
      if (data.status === "running") setTimeout(poll, 2000);
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, [activeJobId]);

  async function runJob(jobKey: string) {
    setJobError("");
    setJobStatus(null);
    const res = await fetch(`${API_URL}/admin/jobs/${jobKey}`, { method: "POST" });
    const body = await res.json();
    if (!res.ok) {
      setJobError(body.detail ?? "failed to start job");
      return;
    }
    setActiveJobId(body.job_id);
  }

  async function addCompany(e: React.FormEvent) {
    e.preventDefault();
    setCompanyMsg("");
    const res = await fetch(`${API_URL}/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: symbol.toUpperCase(), name, sector: sector || null }),
    });
    const body = await res.json();
    if (!res.ok) {
      setCompanyMsg(body.detail ?? "failed to add company");
      return;
    }
    setCompanyMsg(`${body.symbol} added. Run the jobs below to backfill its data.`);
    setSymbol("");
    setName("");
    setSector("");
  }

  const jobRunning = jobStatus?.status === "running";

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto" }}>
      <h1>Admin</h1>
      <p style={{ fontSize: 12, color: "#666" }}>
        Personal tool, no auth (matches the rest of the app - see ADMIN_OPS.md). Runs pipeline jobs directly on the server.
      </p>

      <section style={{ marginTop: 24 }}>
        <h2>Add a company</h2>
        <form onSubmit={addCompany} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <input placeholder="Symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)} style={{ width: 100 }} required />
          <input placeholder="Company name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 220 }} required />
          <input placeholder="Sector (optional)" value={sector} onChange={(e) => setSector(e.target.value)} style={{ width: 140 }} />
          <button type="submit">Add company</button>
        </form>
        {companyMsg && <p style={{ fontSize: 13 }}>{companyMsg}</p>}
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Pipeline jobs</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {JOBS.map((j) => (
            <button key={j.key} onClick={() => runJob(j.key)} disabled={jobRunning}>
              {j.label}
            </button>
          ))}
        </div>
        {jobError && <p style={{ color: "#b00" }}>{jobError}</p>}
        {jobStatus && (
          <div style={{ marginTop: 12 }}>
            <p>
              <strong>{jobStatus.name}</strong>: {jobStatus.status}
              {jobRunning && " (polling...)"}
            </p>
            <pre style={{ background: "#f5f5f5", padding: 12, maxHeight: 300, overflow: "auto", fontSize: 12 }}>
              {jobStatus.log_tail || "(no output yet)"}
            </pre>
          </div>
        )}
      </section>
    </main>
  );
}
