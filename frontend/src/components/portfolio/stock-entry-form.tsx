"use client";

import { XIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { SecurityResults } from "@/components/security-results";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { inr } from "@/lib/format";
import { useDeleteStockTx, useSaveStockTx } from "@/lib/queries";
import type { Security, StockTransaction } from "@/lib/types";
import { cn } from "@/lib/utils";

const BROKERS = ["Groww", "ICICI", "Zerodha"];

type PickedStock = { name: string; symbol: string | null; isin?: string };

export interface StockEntryTarget {
  stock?: PickedStock;
  entry?: StockTransaction;
}

export function StockEntryForm({ open, onOpenChange, target }: { open: boolean; onOpenChange: (o: boolean) => void; target: StockEntryTarget }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        {open && <FormBody key={target.entry?.id ?? target.stock?.symbol ?? "new"} target={target} onDone={() => onOpenChange(false)} />}
      </SheetContent>
    </Sheet>
  );
}

function FormBody({ target, onDone }: { target: StockEntryTarget; onDone: () => void }) {
  const entry = target.entry;
  const [stock, setStock] = useState<PickedStock | null>(target.stock ?? null);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<"buy" | "sell">(entry?.kind ?? "buy");
  const initialBroker = entry?.broker ?? "Zerodha";
  const [broker, setBroker] = useState(BROKERS.includes(initialBroker) ? initialBroker : "Other");
  const [otherBroker, setOtherBroker] = useState(BROKERS.includes(initialBroker) ? "" : initialBroker);
  const [quantity, setQuantity] = useState(entry ? String(entry.quantity) : "");
  const [price, setPrice] = useState(entry ? String(entry.price) : "");
  const [date, setDate] = useState(entry?.date ?? new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState(entry?.note ?? "");
  const [error, setError] = useState<string | null>(null);
  const save = useSaveStockTx();
  const remove = useDeleteStockTx();

  const q = Number(quantity), p = Number(price);

  const pick = (s: Security) => {
    setError(null);
    setStock({ name: s.name, symbol: s.nse_symbol ?? s.bse_symbol, isin: s.isin });
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const brokerName = broker === "Other" ? otherBroker.trim() : broker;
    if (!stock) return setError("Choose the stock or ETF first.");
    if (!(q > 0)) return setError("Enter the number of shares.");
    if (!(p >= 0) || price === "") return setError("Enter the price per share.");
    if (!brokerName) return setError("Enter where you hold it.");
    setError(null);
    save.mutate(
      {
        id: entry?.id,
        input: {
          ...(stock.isin ? { isin: stock.isin } : { symbol: stock.symbol! }),
          broker: brokerName, kind, quantity: q, price: p, date: date || null, note: note || null,
        },
      },
      {
        onSuccess: (res) => {
          const tracked = res && typeof res === "object" && "newly_tracked" in res && res.newly_tracked;
          toast.success(entry ? "Entry updated" : kind === "buy" ? (tracked ? `Purchase added. Loading ${stock.symbol}'s prices.` : "Purchase added") : "Sale recorded");
          onDone();
        },
        onError: (err) => setError(err.message),
      },
    );
  };

  return (
    <form onSubmit={submit} className="flex min-h-full flex-col">
      <SheetHeader>
        <SheetTitle>{entry ? "Edit entry" : "Add a stock or ETF entry"}</SheetTitle>
        <SheetDescription>Record a purchase or sale at any broker. Holdings, returns and XIRR come from these entries.</SheetDescription>
      </SheetHeader>
      <div className="flex-1 space-y-5 px-4">
        <div className="space-y-2">
          <Label>Stock or ETF</Label>
          {stock ? (
            <div className="flex items-center justify-between gap-2 rounded-md border border-input bg-surface px-3 py-2">
              <div className="min-w-0">
                <div className="truncate font-medium">{stock.name}</div>
                <div className="text-xs text-muted-foreground">{stock.symbol}</div>
              </div>
              {!entry && (
                <button type="button" onClick={() => setStock(null)} className="rounded p-1 text-muted-foreground hover:text-foreground" aria-label="Choose a different stock">
                  <XIcon className="size-4" />
                </button>
              )}
            </div>
          ) : (
            <div className="rounded-md border border-input bg-surface">
              <SecurityResults query={query} onQueryChange={setQuery} onSelect={pick} autoFocus />
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
          {broker === "Other" && <Input aria-label="Broker name" value={otherBroker} onChange={(e) => setOtherBroker(e.target.value)} placeholder="e.g. Upstox" maxLength={40} />}
        </fieldset>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="st-qty">Shares</Label>
            <Input id="st-qty" inputMode="decimal" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="st-price">Price per share (₹)</Label>
            <Input id="st-price" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} />
          </div>
        </div>
        {q > 0 && p > 0 && <p className="num -mt-2 text-sm text-muted-foreground">{kind === "buy" ? "Total paid" : "Total received"} {inr(q * p, { precise: true })}.</p>}

        <div className="space-y-2">
          <Label htmlFor="st-date">Date</Label>
          <Input id="st-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="st-note">Note <span className="font-normal text-muted-foreground">(optional)</span></Label>
          <Input id="st-note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} />
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
