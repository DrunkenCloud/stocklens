
const inrFull = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const inrPrecise = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const plain = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });

export const DASH = "–";

export function inr(v: number | null | undefined, opts: { precise?: boolean; signed?: boolean } = {}): string {
  if (v === null || v === undefined || Number.isNaN(v)) return DASH;
  const s = (opts.precise ? inrPrecise : inrFull).format(Math.abs(v));
  if (opts.signed) return `${v > 0 ? "+" : v < 0 ? "−" : ""}${s}`;
  return v < 0 ? `−${s}` : s;
}

export function inrCompact(v: number | null | undefined): string {
  if (v === null || v === undefined) return DASH;
  const a = Math.abs(v);
  const sign = v < 0 ? "−" : "";
  if (a >= 1e7) return `${sign}₹${(a / 1e7).toLocaleString("en-IN", { maximumFractionDigits: a >= 1e9 ? 0 : 2, minimumFractionDigits: a >= 1e9 ? 0 : 2 })} Cr`;
  if (a >= 1e5) return `${sign}₹${(a / 1e5).toFixed(2)} L`;
  return `${sign}${inrFull.format(a)}`;
}

export function pct(v: number | null | undefined, opts: { signed?: boolean; digits?: number } = {}): string {
  if (v === null || v === undefined || Number.isNaN(v)) return DASH;
  const s = `${Math.abs(v).toFixed(opts.digits ?? 2)}%`;
  if (opts.signed) return `${v > 0 ? "+" : v < 0 ? "−" : ""}${s}`;
  return v < 0 ? `−${s}` : s;
}

export function num(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return DASH;
  return v.toLocaleString("en-IN", { maximumFractionDigits: digits });
}

export function qty(v: number): string {
  return plain.format(v);
}

export function tone(v: number | null | undefined): string {
  if (!v) return "text-muted-foreground";
  return v > 0 ? "text-gain" : "text-loss";
}

export function date(iso: string | null | undefined): string {
  if (!iso) return DASH;
  return new Date(iso.length === 10 ? `${iso}T00:00:00` : iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export function time(iso: string | null | undefined): string {
  if (!iso) return DASH;
  return new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
}

export function ago(iso: string | null | undefined): string {
  if (!iso) return DASH;
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} h ago`;
  return time(iso);
}

const BROKER_COLORS: Record<string, string> = {
  ICICI: "var(--broker-icici)",
  Zerodha: "var(--broker-zerodha)",
  Groww: "var(--broker-groww)",
};

export function brokerColor(broker: string): string {
  return BROKER_COLORS[broker] ?? "var(--broker-other)";
}
