"use client";

import { XIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useDebounced } from "@/hooks/use-debounced";
import { inr, num } from "@/lib/format";
import { useDeleteMfTx, useMfSearch, useSaveMfTx } from "@/lib/queries";
import type { MfScheme, MfTransaction } from "@/lib/types";
import { cn } from "@/lib/utils";

const BROKERS = ["Groww", "ICICI", "Zerodha"];

type PickedFund = { code: number; label: string; nav: number | null };

export interface MfFormTarget {
  fund?: PickedFund;
  entry?: MfTransaction;
}

export function MfForm({ open, onOpenChange, target }: { open: boolean; onOpenChange: (o: boolean) => void; target: MfFormTarget }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        {open && <FormBody key={target.entry?.id ?? target.fund?.code ?? "new"} target={target} onDone={() => onOpenChange(false)} />}
      </SheetContent>
    </Sheet>
  );
}

function FundPicker({ onPick }: { onPick: (s: MfScheme) => void }) {
  const [query, setQuery] = useState("");
  const debounced = useDebounced(query);
  const { data, isFetching } = useMfSearch(debounced);
  const results = debounced.trim().length > 1 ? (data ?? []) : [];
  return (
    <Command shouldFilter={false} className="bg-transparent">
      <CommandInput value={query} onValueChange={setQuery} placeholder="Fund name, e.g. parag parikh flexi" autoFocus />
      <CommandList className="max-h-64">
        {debounced.trim().length > 1 && !isFetching && <CommandEmpty>No fund matches “{debounced}”.</CommandEmpty>}
        {results.length > 0 && (
          <CommandGroup>
            {results.map((s) => (
              <CommandItem key={s.code} value={String(s.code)} onSelect={() => onPick(s)} className="items-start py-2">
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium">{s.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {[s.plan, s.option, s.category?.replace(/^.* - /, "")].filter(Boolean).join(", ")}
                  </div>
                </div>
                {s.held && <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-xs">Held</span>}
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </Command>
  );
}

function FormBody({ target, onDone }: { target: MfFormTarget; onDone: () => void }) {
  const entry = target.entry;
  const [fund, setFund] = useState<PickedFund | null>(target.fund ?? null);
  const [kind, setKind] = useState<"buy" | "sell">(entry?.kind ?? "buy");
  const initialBroker = entry?.broker ?? "Groww";
  const [broker, setBroker] = useState(BROKERS.includes(initialBroker) ? initialBroker : "Other");
  const [otherBroker, setOtherBroker] = useState(BROKERS.includes(initialBroker) ? "" : initialBroker);
  const [amount, setAmount] = useState(entry ? String(entry.amount) : "");
  const [units, setUnits] = useState(entry ? String(entry.units) : "");
  const [currentValue, setCurrentValue] = useState("");
  const [date, setDate] = useState(entry?.date ?? "");
  const [error, setError] = useState<string | null>(null);
  const save = useSaveMfTx();
  const remove = useDeleteMfTx();

  const estimatedUnits = !units && Number(currentValue) > 0 && fund?.nav ? Number(currentValue) / fund.nav : null;
  const finalUnits = Number(units) || estimatedUnits || 0;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const brokerName = broker === "Other" ? otherBroker.trim() : broker;
    if (!fund) return setError("Choose the fund first.");
    if (!(Number(amount) >= 0) || amount === "") return setError(kind === "buy" ? "Enter how much you invested." : "Enter how much you received.");
    if (!(finalUnits > 0)) return setError("Enter the units, or the current value so units can be worked out.");
    if (!brokerName) return setError("Enter where you hold it.");
    setError(null);
    save.mutate(
      {
        id: entry?.id,
        input: { code: fund.code, broker: brokerName, kind, units: Number(finalUnits.toFixed(4)), amount: Number(amount), date: date || null },
      },
      {
        onSuccess: () => {
          toast.success(entry ? "Entry updated" : kind === "buy" ? "Purchase added" : "Sale recorded");
          onDone();
        },
        onError: (err) => setError(err.message),
      },
    );
  };

  return (
    <form onSubmit={submit} className="flex min-h-full flex-col">
      <SheetHeader>
        <SheetTitle>{entry ? "Edit entry" : "Add mutual fund entry"}</SheetTitle>
        <SheetDescription>Record what you bought or sold. Holdings and returns are worked out from these entries.</SheetDescription>
      </SheetHeader>
      <div className="flex-1 space-y-5 px-4">
        <div className="space-y-2">
          <Label>Fund</Label>
          {fund ? (
            <div className="flex items-center justify-between gap-2 rounded-md border border-input bg-surface px-3 py-2">
              <div className="min-w-0">
                <div className="truncate font-medium">{fund.label}</div>
                {fund.nav !== null && <div className="num text-xs text-muted-foreground">NAV {num(fund.nav, 4)}</div>}
              </div>
              {!entry && (
                <button type="button" onClick={() => setFund(null)} className="rounded p-1 text-muted-foreground hover:text-foreground" aria-label="Choose a different fund">
                  <XIcon className="size-4" />
                </button>
              )}
            </div>
          ) : (
            <div className="rounded-md border border-input bg-surface">
              <FundPicker onPick={(s) => setFund({ code: s.code, label: s.plan ? `${s.name} (${s.plan})` : s.name, nav: s.nav })} />
            </div>
          )}
        </div>

        <div className="flex gap-1.5" role="group" aria-label="Entry type">
          {(["buy", "sell"] as const).map((k) => (
            <button key={k} type="button" aria-pressed={kind === k} onClick={() => setKind(k)}
              className={cn("flex-1 rounded-md border border-input px-3 py-1.5 text-sm", kind === k && "border-foreground bg-foreground text-background")}>
              {k === "buy" ? "Bought" : "Sold"}
            </button>
          ))}
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Held at</legend>
          <div className="flex gap-1.5">
            {[...BROKERS, "Other"].map((b) => (
              <button key={b} type="button" aria-pressed={broker === b} onClick={() => setBroker(b)}
                className={cn("flex-1 rounded-md border border-input px-2 py-1.5 text-sm", broker === b && "border-foreground bg-foreground text-background")}>
                {b}
              </button>
            ))}
          </div>
          {broker === "Other" && <Input aria-label="Where you hold it" value={otherBroker} onChange={(e) => setOtherBroker(e.target.value)} placeholder="e.g. Kuvera, AMC direct" />}
        </fieldset>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="mf-amount">{kind === "buy" ? "Amount invested (₹)" : "Amount received (₹)"}</Label>
            <Input id="mf-amount" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="mf-units">Units</Label>
            <Input id="mf-units" inputMode="decimal" value={units} onChange={(e) => setUnits(e.target.value)} placeholder={estimatedUnits ? estimatedUnits.toFixed(3) : ""} />
          </div>
        </div>
        {!units && !entry && (
          <div className="space-y-2">
            <Label htmlFor="mf-current">Don&apos;t know the units? Current value (₹)</Label>
            <Input id="mf-current" inputMode="decimal" value={currentValue} onChange={(e) => setCurrentValue(e.target.value)} />
            <p className="num text-xs text-muted-foreground">
              {estimatedUnits ? `About ${estimatedUnits.toFixed(3)} units at today's NAV.` : "Units are worked out as current value ÷ latest NAV."}
            </p>
          </div>
        )}
        {kind === "buy" && Number(amount) > 0 && finalUnits > 0 && (
          <p className="num -mt-2 text-sm text-muted-foreground">Average cost {inr(Number(amount) / finalUnits, { precise: true })} per unit.</p>
        )}

        <div className="space-y-2">
          <Label htmlFor="mf-date">Date <span className="font-normal text-muted-foreground">(optional)</span></Label>
          <Input id="mf-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
        {error && <p role="alert" className="text-sm text-loss">{error}</p>}
      </div>
      <SheetFooter className="flex-row gap-2">
        {entry && (
          <Button type="button" variant="outline" className="text-loss" disabled={remove.isPending}
            onClick={() => remove.mutate(entry.id, { onSuccess: () => { toast.success("Entry deleted"); onDone(); }, onError: (e) => setError(e.message) })}>
            Delete
          </Button>
        )}
        <Button type="submit" disabled={save.isPending} className="flex-1">
          {save.isPending ? "Saving…" : entry ? "Save changes" : kind === "buy" ? "Add purchase" : "Record sale"}
        </Button>
      </SheetFooter>
    </form>
  );
}
