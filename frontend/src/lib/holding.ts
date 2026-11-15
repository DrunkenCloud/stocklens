const DROP = /\b(fund of funds?|fund|prudential|oswal|sun life|plan|growth|option)\b/gi;

export function shortFundName(name: string): string {
  const cleaned = name
    .replace(/\(.*?\)/g, "")
    .replace(/aditya birla/i, "ABSL")
    .replace(DROP, "")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned.split(" ").slice(0, 3).join(" ");
}

export function holdingHref(h: { kind: string; symbol: string }): string {
  return h.kind === "mf" ? `/fund/?code=${h.symbol}` : `/stock/?s=${encodeURIComponent(h.symbol)}`;
}

export function holdingTitle(h: { kind: string; symbol: string; name: string }): string {
  return h.kind === "mf" ? h.name : h.symbol;
}
