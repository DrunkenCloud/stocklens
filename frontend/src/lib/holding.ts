const DROP = /\b(fund of funds?|fund|prudential|oswal|sun life|plan|growth|option)\b/gi;

export function shortFundName(name: string): string {
  const cleaned = name
    .replace(/\(.*?\)/g, "")
    .replace(/aditya birla/i, "ABSL")
    .replace(DROP, "")
    .replace(/\s+/g, " ")
    .trim();
  const words = cleaned.split(" ").slice(0, 3);
  while (words.length > 1 && /^(and|&|of|the|-)$/i.test(words[words.length - 1])) words.pop();
  return words.join(" ");
}

export function holdingHref(h: { kind: string; symbol: string }): string {
  return h.kind === "mf" ? `/fund/?code=${h.symbol}` : `/stock/?s=${encodeURIComponent(h.symbol)}`;
}

export function holdingTitle(h: { kind: string; symbol: string; name: string }): string {
  return h.kind === "mf" ? h.name : h.symbol;
}
