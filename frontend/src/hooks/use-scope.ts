"use client";

import { useSyncExternalStore } from "react";

import type { Scope } from "@/lib/types";

export const SCOPES: { value: Scope; label: string }[] = [
  { value: "all", label: "Everything" },
  { value: "stocks", label: "Stocks & ETFs" },
  { value: "mf", label: "Mutual funds" },
];
const SCOPE_KEY = "stocklens.scope";

const scopeListeners = new Set<() => void>();
let scopeMemory: Scope = "all";

function readScope(): Scope {
  try {
    const saved = localStorage.getItem(SCOPE_KEY);
    if (SCOPES.some((s) => s.value === saved)) return saved as Scope;
  } catch {}
  return scopeMemory;
}

function subscribeScope(onChange: () => void) {
  scopeListeners.add(onChange);
  window.addEventListener("storage", onChange);
  return () => {
    scopeListeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function useScope(): [Scope, (s: Scope) => void] {
  const scope = useSyncExternalStore(subscribeScope, readScope, () => "all" as Scope);
  const update = (next: Scope) => {
    scopeMemory = next;
    try {
      localStorage.setItem(SCOPE_KEY, next);
    } catch {}
    scopeListeners.forEach((l) => l());
  };
  return [scope, update];
}

