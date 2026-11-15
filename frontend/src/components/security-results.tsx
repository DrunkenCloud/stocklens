"use client";

import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { useDebounced } from "@/hooks/use-debounced";
import { useSecuritySearch } from "@/lib/queries";
import type { Security } from "@/lib/types";

/** Search box + results over every NSE/BSE equity. Server-side matching, so cmdk's own filter is off. */
export function SecurityResults({
  query, onQueryChange, onSelect, placeholder = "Company name, NSE symbol or BSE code", autoFocus,
}: {
  query: string;
  onQueryChange: (q: string) => void;
  onSelect: (s: Security) => void;
  placeholder?: string;
  autoFocus?: boolean;
}) {
  const debounced = useDebounced(query);
  const { data, isFetching, isError, error } = useSecuritySearch(debounced);
  const results = debounced.trim() ? (data ?? []) : [];

  return (
    <Command shouldFilter={false} className="bg-transparent">
      <CommandInput value={query} onValueChange={onQueryChange} placeholder={placeholder} autoFocus={autoFocus} />
      <CommandList className="max-h-[min(60dvh,24rem)]">
        {debounced.trim() && !isFetching && !isError && <CommandEmpty>No listed company matches “{debounced}”.</CommandEmpty>}
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
                    {!s.nse_symbol && <span className="ml-2">BSE only</span>}
                  </div>
                </div>
                {s.tracked && <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">Tracked</span>}
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </Command>
  );
}
