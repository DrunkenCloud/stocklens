"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { api } from "@/lib/api";
import type {
  Benchmarks, Insights, Tax, Company, Exposure, ExposureBreakdown, Fund, Growth, JobRun, MfScheme, MfTransactionInput, Portfolio, Scope, StockTransaction, StockTransactionInput, PricePoint, Returns, ScreenRow, Security, Status, Stock,
} from "@/lib/types";

export const keys = {
  status: ["status"] as const,
  portfolio: (scope: Scope) => ["portfolio", scope] as const,
  growth: (days: number, scope: Scope) => ["growth", days, scope] as const,
  entries: (symbol: string) => ["entries", symbol] as const,
  exposure: (scope: Scope) => ["exposure", scope] as const,
  breakdown: (scope: Scope, key: string) => ["exposure", scope, key] as const,
  mfSearch: (q: string) => ["mf-search", q] as const,
  fund: (code: number) => ["fund", code] as const,
  search: (q: string) => ["search", q] as const,
  stock: (s: string) => ["stock", s] as const,
  prices: (s: string, from: string) => ["prices", s, from] as const,
  returns: (s: string, from: string, amount: number) => ["returns", s, from, amount] as const,
  screen: (p: string) => ["screen", p] as const,
  runs: ["runs"] as const,
  run: (id: number) => ["run", id] as const,
  companies: ["companies"] as const,
  benchmarks: ["benchmarks"] as const,
  insights: ["insights"] as const,
  tax: ["tax"] as const,
};

export function useStatus() {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: keys.status,
    queryFn: () => api<Status>("/status"),
    refetchInterval: (q) => (q.state.data?.running.length ? 3000 : q.state.data?.live_at ? 30000 : 60000),
  });
  const wasRunning = useRef(false);
  const lastLive = useRef<string | null>(null);
  const running = (query.data?.running.length ?? 0) > 0;
  const liveAt = query.data?.live_at ?? null;
  useEffect(() => {
    if (wasRunning.current && !running) qc.invalidateQueries();
    wasRunning.current = running;
  }, [running, qc]);
  useEffect(() => {
    if (liveAt && lastLive.current && liveAt !== lastLive.current) {
      for (const key of ["portfolio", "growth", "exposure", "prices", "stock", "benchmarks", "insights", "tax"]) qc.invalidateQueries({ queryKey: [key] });
    }
    lastLive.current = liveAt;
  }, [liveAt, qc]);
  return query;
}

export const usePortfolio = (scope: Scope = "all") =>
  useQuery({ queryKey: keys.portfolio(scope), queryFn: () => api<Portfolio>(`/portfolio?scope=${scope}`), placeholderData: keepPreviousData });

export const usePortfolioGrowth = (days: number, scope: Scope = "all") =>
  useQuery({
    queryKey: keys.growth(days, scope),
    queryFn: () => api<Growth>(`/portfolio/growth?days=${days}&scope=${scope}`),
    placeholderData: keepPreviousData,
  });

export function useSecuritySearch(q: string) {
  const term = q.trim();
  return useQuery({
    queryKey: keys.search(term),
    queryFn: () => api<Security[]>(`/securities/search?q=${encodeURIComponent(term)}&limit=12`),
    enabled: term.length > 0,
    placeholderData: keepPreviousData,
    staleTime: 5 * 60_000,
  });
}

export function useMfSearch(q: string) {
  const term = q.trim();
  return useQuery({
    queryKey: keys.mfSearch(term),
    queryFn: () => api<MfScheme[]>(`/mf/search?q=${encodeURIComponent(term)}&limit=12`),
    enabled: term.length > 1,
    placeholderData: keepPreviousData,
    staleTime: 5 * 60_000,
  });
}

export const useFund = (code: number) =>
  useQuery({ queryKey: keys.fund(code), queryFn: () => api<Fund>(`/mf/${code}`), enabled: code > 0, retry: false });

export function useSaveMfTx() {
  const done = useInvalidateAll();
  return useMutation({
    mutationFn: ({ id, input }: { id?: string; input: MfTransactionInput }) =>
      id ? api(`/mf/transactions/${id}`, { method: "PUT", json: input }) : api("/mf/transactions", { method: "POST", json: input }),
    onSuccess: done,
  });
}

export function useDeleteMfTx() {
  const done = useInvalidateAll();
  return useMutation({ mutationFn: (id: string) => api(`/mf/transactions/${id}`, { method: "DELETE" }), onSuccess: done });
}

export const useStock = (symbol: string) =>
  useQuery({ queryKey: keys.stock(symbol), queryFn: () => api<Stock>(`/stocks/${encodeURIComponent(symbol)}`), enabled: !!symbol, retry: false });

export const usePrices = (symbol: string, from: string) =>
  useQuery({
    queryKey: keys.prices(symbol, from),
    queryFn: () => api<PricePoint[]>(`/prices/${encodeURIComponent(symbol)}?from=${from}`),
    enabled: !!symbol,
    placeholderData: keepPreviousData,
    retry: false,
  });

export const useReturns = (symbol: string, from: string, amount: number) =>
  useQuery({
    queryKey: keys.returns(symbol, from, amount),
    queryFn: () => api<Returns>(`/prices/${encodeURIComponent(symbol)}/returns?from=${from}&amount=${amount}`),
    enabled: !!symbol && !!from && amount > 0,
    placeholderData: keepPreviousData,
    retry: false,
  });

export const useScreen = (params: URLSearchParams) =>
  useQuery({
    queryKey: keys.screen(params.toString()),
    queryFn: () => api<ScreenRow[]>(`/screen?${params}`),
    placeholderData: keepPreviousData,
  });

export const useCompanies = () => useQuery({ queryKey: keys.companies, queryFn: () => api<Company[]>("/companies") });

export const useRuns = () =>
  useQuery({
    queryKey: keys.runs,
    queryFn: () => api<{ jobs: string[]; runs: JobRun[] }>("/admin/jobs?limit=40"),
    refetchInterval: (q) => (q.state.data?.runs.some((r) => r.status === "running") ? 2000 : false),
  });

export const useRun = (id: number | null) =>
  useQuery({
    queryKey: keys.run(id ?? 0),
    queryFn: () => api<JobRun>(`/admin/jobs/${id}`),
    enabled: id !== null,
    refetchInterval: (q) => (q.state.data?.status === "running" ? 2000 : false),
  });

function useInvalidateAll() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries();
}

export const useExposure = (scope: Scope) =>
  useQuery({ queryKey: keys.exposure(scope), queryFn: () => api<Exposure>(`/portfolio/exposure?scope=${scope}`), placeholderData: keepPreviousData });

export const useExposureBreakdown = (scope: Scope, key: string | null) =>
  useQuery({
    queryKey: keys.breakdown(scope, key ?? ""),
    queryFn: () => api<ExposureBreakdown>(`/portfolio/exposure/breakdown?scope=${scope}&key=${encodeURIComponent(key!)}`),
    enabled: !!key,
  });

export const useStockEntries = (symbol: string) =>
  useQuery({
    queryKey: keys.entries(symbol),
    queryFn: () => api<StockTransaction[]>(`/stock-transactions?symbol=${encodeURIComponent(symbol)}`),
    enabled: !!symbol,
  });

export function useSaveStockTx() {
  const done = useInvalidateAll();
  return useMutation({
    mutationFn: ({ id, input }: { id?: string; input: StockTransactionInput }) =>
      id
        ? api(`/stock-transactions/${id}`, { method: "PUT", json: input })
        : api<{ symbol: string; newly_tracked: boolean }>("/stock-transactions", { method: "POST", json: input }),
    onSuccess: done,
  });
}

export function useDeleteStockTx() {
  const done = useInvalidateAll();
  return useMutation({ mutationFn: (id: string) => api(`/stock-transactions/${id}`, { method: "DELETE" }), onSuccess: done });
}

export function useTrack() {
  const done = useInvalidateAll();
  return useMutation({
    mutationFn: (isin: string) => api<{ symbol: string; run_id: number }>("/companies", { method: "POST", json: { isin } }),
    onSuccess: done,
  });
}

export function useTriggerJob() {
  const done = useInvalidateAll();
  return useMutation({
    mutationFn: (name: string) => api<{ run_id: number }>(`/admin/jobs/${name}`, { method: "POST" }),
    onSuccess: done,
  });
}

export async function openIciciLogin() {
  const { url } = await api<{ url: string }>("/breeze/login-url");
  window.location.href = url;
}

export const useBenchmarks = () => useQuery({ queryKey: keys.benchmarks, queryFn: () => api<Benchmarks>("/portfolio/benchmarks") });

export const useInsights = () => useQuery({ queryKey: keys.insights, queryFn: () => api<Insights>("/portfolio/insights") });

export const useTax = () => useQuery({ queryKey: keys.tax, queryFn: () => api<Tax>("/tax") });
