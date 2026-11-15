"use client";

import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { useDebounced } from "@/hooks/use-debounced";
import { useMfSearch, useSecuritySearch } from "@/lib/queries";
import type { MfScheme, Security } from "@/lib/types";

export function SecurityResults({
  query, onQueryChange, onSelect, onSelectFund, placeholder = "Company name, NSE symbol or BSE code", autoFocus,
}: {
  query: string;
  onQueryChange: (q: string) => void;
  onSelect: (s: Security) => void;
  onSelectFund?: (f: MfScheme) => void;
  placeholder?: string;
  autoFocus?: boolean;
}) {
  const debounced = useDebounced(query);
  const { data, isFetching, isError, error } = useSecuritySearch(debounced);
  const results = debounced.trim() ? (data ?? []) : [];
  const funds = useMfSearch(onSelectFund ? debounced : "");
  const fundResults = onSelectFund && debounced.trim().length > 1 ? (funds.data ?? []) : [];

  return (
    <Command shouldFilter={false} className="bg-transparent">
      <CommandInput value={query} onValueChange={onQueryChange} placeholder={placeholder} autoFocus={autoFocus} />
      <CommandList className="max-h-[min(60dvh,24rem)]">
        {debounced.trim() && !isFetching && !funds.isFetching && !isError && <CommandEmpty>No listed company matches “{debounced}”.</CommandEmpty>}
        {isError && <p className="px-3 py-6 text-center text-sm text-loss">{error.message}</p>}
        {results.length > 0 && (
          <CommandGroup>
            {results.map((s) => (
              <CommandItem key={s.isin} value={s.isin} onSelect={() => onSelect(s)} className="items-start gap-3 py-2">
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium">{s.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {s.nse_symbol ?? s.bse_symbol}
                    <span className="ml-2">{s.exchanges.join(" + ")}</span>
                    {s.kind === "etf" && <span className="ml-2">ETF</span>}
                  </div>
                </div>
                {s.tracked && <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">Tracked</span>}
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {fundResults.length > 0 && (
          <CommandGroup heading="Mutual funds">
            {fundResults.slice(0, 6).map((f) => (
              <CommandItem key={f.code} value={`mf-${f.code}`} onSelect={() => onSelectFund?.(f)} className="items-start gap-3 py-2">
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium">{f.name}</div>
                  <div className="text-xs text-muted-foreground">{[f.plan, f.option, f.category?.replace(/^.* - /, "")].filter(Boolean).join(", ")}</div>
                </div>
                {f.held && <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">Held</span>}
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </Command>
  );
}
