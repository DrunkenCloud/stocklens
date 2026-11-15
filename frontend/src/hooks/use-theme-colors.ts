"use client";

import { useTheme } from "next-themes";
import { useMemo } from "react";

const NAMES = ["--gain", "--loss", "--border", "--muted-foreground", "--text-tertiary", "--foreground", "--surface"] as const;
export type ThemeColors = Record<(typeof NAMES)[number], string>;

export function useThemeColors(): ThemeColors | null {
  const { resolvedTheme } = useTheme();
  return useMemo(() => {
    if (typeof window === "undefined" || !resolvedTheme) return null;
    const css = getComputedStyle(document.documentElement);
    return Object.fromEntries(NAMES.map((n) => [n, css.getPropertyValue(n).trim()])) as ThemeColors;
  }, [resolvedTheme]);
}

export function withAlpha(hex: string, alpha: number): string {
  const n = parseInt(hex.replace("#", ""), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}
