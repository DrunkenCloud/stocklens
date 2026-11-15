"use client";

import { SearchIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SecurityResults } from "@/components/security-results";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

export function stockHref(s: { nse_symbol: string | null; isin: string }) {
  return s.nse_symbol ? `/stock/?s=${encodeURIComponent(s.nse_symbol)}` : `/stock/?isin=${s.isin}`;
}

export function StockSearch({ className }: { className?: string }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLElement && e.target.closest("input, textarea, [contenteditable]");
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
        e.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          "flex h-9 items-center gap-2 rounded-md border border-input bg-surface px-3 text-sm text-muted-foreground transition-colors hover:border-ring/60 focus-visible:outline-2 focus-visible:outline-ring",
          className,
        )}
        aria-label="Search stocks"
      >
        <SearchIcon className="size-4 shrink-0" />
        <span className="hidden flex-1 text-left sm:inline">Search any NSE or BSE stock</span>
        <kbd className="hidden rounded border border-border px-1.5 text-[11px] lg:inline">Ctrl K</kbd>
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="top-[12dvh] translate-y-0 gap-0 overflow-hidden p-0 sm:max-w-lg" showCloseButton={false}>
          <DialogTitle className="sr-only">Search stocks</DialogTitle>
          <SecurityResults
            autoFocus
            query={query}
            onQueryChange={setQuery}
            onSelect={(s) => {
              setOpen(false);
              setQuery("");
              router.push(stockHref(s));
            }}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}
