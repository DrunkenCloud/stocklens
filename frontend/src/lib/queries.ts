"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { api } from "@/lib/api";
import type {
  Company, HistoryPoint, HoldingInput, JobRun, Portfolio, PricePoint, Returns, ScreenRow, Security, Status, Stock,
} from "@/lib/types";

export const keys = {
  status: ["status"] as const,
  portfolio: ["portfolio"] as const,
  history: (days: number) => ["history", days] as const,
  search: (q: string) => ["search", q] as const,
  stock: (s: string) => ["stock", s] as const,
  prices: (s: string, from: string) => ["prices", s, from] as const,
  returns: (s: string, from: string, amount: number) => ["returns", s, from, amount] as const,
  screen: (p: string) => ["screen", p] as const,
  runs: ["runs"] as const,
  run: (id: number) => ["run", id] as const,
  companies: ["companies"] as const,
};

export function useStatus() {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: keys.status,
    queryFn: () => api<Status>("/status"),
    refetchInterval: (q) => (q.state.data?.running.length ? 3000 : 60000),
  });
  const wasRunning = useRef(false);
  const running = (query.data?.running.length ?? 0) > 0;
  useEffect(() => {
    if (wasRunning.current && !running) qc.invalidateQueries();
    wasRunning.current = running;
  }, [running, qc]);
  return query;
}

export const usePortfolio = () => useQuery({ queryKey: keys.portfolio, queryFn: () => api<Portfolio>("/portfolio") });

export const usePortfolioHistory = (days: number) =>
  useQuery({
    queryKey: keys.history(days),
    queryFn: () => api<HistoryPoint[]>(`/portfolio/history?days=${days}`),
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

export function useSaveHolding() {
  const done = useInvalidateAll();
  return useMutation({
    mutationFn: ({ id, input }: { id?: string; input: HoldingInput }) =>
      id ? api(`/portfolio/${id}`, { method: "PUT", json: input }) : api<{ symbol: string; newly_tracked: boolean }>("/portfolio", { method: "POST", json: input }),
    onSuccess: done,
  });
}

export function useDeleteHolding() {
  const done = useInvalidateAll();
  return useMutation({ mutationFn: (id: string) => api(`/portfolio/${id}`, { method: "DELETE" }), onSuccess: done });
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
