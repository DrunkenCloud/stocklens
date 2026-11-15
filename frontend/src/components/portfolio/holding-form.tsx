"use client";

import { XIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { SecurityResults } from "@/components/security-results";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { inr } from "@/lib/format";
import { useDeleteHolding, useSaveHolding } from "@/lib/queries";
import type { Holding, Security } from "@/lib/types";
import { cn } from "@/lib/utils";

const BROKERS = ["Zerodha", "Groww"];

type Picked = { name: string; symbol: string | null; isin?: string };

export function HoldingForm({ open, onOpenChange, holding }: { open: boolean; onOpenChange: (o: boolean) => void; holding: Holding | null }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        {open && <FormBody key={holding?.id ?? "new"} holding={holding} onDone={() => onOpenChange(false)} />}
      </SheetContent>
    </Sheet>
  );
}

function FormBody({ holding, onDone }: { holding: Holding | null; onDone: () => void }) {
  const [stock, setStock] = useState<Picked | null>(holding ? { name: holding.name, symbol: holding.symbol } : null);
  const [query, setQuery] = useState("");
  const [shares, setShares] = useState(holding ? String(holding.quantity) : "");
  const [invested, setInvested] = useState(holding ? String(holding.invested) : "");
  const initialBroker = holding?.broker ?? "Zerodha";
  const [broker, setBroker] = useState(BROKERS.includes(initialBroker) ? initialBroker : "Other");
  const [otherBroker, setOtherBroker] = useState(BROKERS.includes(initialBroker) ? "" : initialBroker);
  const [buyDate, setBuyDate] = useState(holding?.buy_date ?? "");
  const [note, setNote] = useState(holding?.note ?? "");
  const [error, setError] = useState<string | null>(null);

  const save = useSaveHolding();
  const remove = useDeleteHolding();

  const q = Number(shares), amt = Number(invested);
  const avg = q > 0 && amt > 0 ? amt / q : null;

  const pick = (s: Security) => {
    setError(null);
    setStock({ name: s.name, symbol: s.nse_symbol ?? s.bse_symbol, isin: s.isin });
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const brokerName = broker === "Other" ? otherBroker.trim() : broker;
    if (!stock) return setError("Choose the stock first.");
    if (!(q > 0)) return setError("Enter how many shares you hold.");
    if (!(amt > 0)) return setError("Enter the total amount you paid for these shares.");
    if (!brokerName) return setError("Enter the broker's name.");
    setError(null);
    save.mutate(
      {
        id: holding?.id,
        input: { ...(stock.isin ? { isin: stock.isin } : { symbol: stock.symbol! }), quantity: q, invested: amt, broker: brokerName, buy_date: buyDate || null, note: note || null },
      },
      {
        onSuccess: (res) => {
          const tracked = res && typeof res === "object" && "newly_tracked" in res && res.newly_tracked;
          toast.success(holding ? "Holding updated" : tracked ? `Holding added. Loading ${stock.symbol}'s prices in the background.` : "Holding added");
          onDone();
        },
        onError: (err) => setError(err.message),
      },
    );
  };

  const del = () =>
    remove.mutate(holding!.id, {
      onSuccess: () => { toast.success("Holding deleted"); onDone(); },
      onError: (err) => setError(err.message),
    });

  return (
    <form onSubmit={submit} className="flex min-h-full flex-col">
      <SheetHeader>
        <SheetTitle>{holding ? "Edit holding" : "Add a holding"}</SheetTitle>
        <SheetDescription>For stocks at Zerodha, Groww or elsewhere. ICICI holdings sync on their own when you log in.</SheetDescription>
      </SheetHeader>

      <div className="flex-1 space-y-5 px-4">
        <div className="space-y-2">
          <Label>Stock</Label>
          {stock ? (
            <div className="flex items-center justify-between gap-2 rounded-md border border-input bg-surface px-3 py-2">
              <div className="min-w-0">
                <div className="truncate font-medium">{stock.name}</div>
                <div className="text-xs text-muted-foreground">{stock.symbol}</div>
              </div>
              <button type="button" onClick={() => setStock(null)} className="rounded p-1 text-muted-foreground hover:text-foreground" aria-label="Choose a different stock">
                <XIcon className="size-4" />
              </button>
            </div>
          ) : (
            <div className="rounded-md border border-input bg-surface">
              <SecurityResults query={query} onQueryChange={setQuery} onSelect={pick} autoFocus />
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="shares">Shares</Label>
            <Input id="shares" inputMode="decimal" value={shares} onChange={(e) => setShares(e.target.value)} placeholder="10" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="invested">Total invested (₹)</Label>
            <Input id="invested" inputMode="decimal" value={invested} onChange={(e) => setInvested(e.target.value)} placeholder="25000" />
          </div>
        </div>
        <p className="num -mt-2 text-sm text-muted-foreground">
          {avg ? <>Works out to {inr(avg, { precise: true })} per share.</> : "Enter both to see your average cost per share."}
        </p>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Broker</legend>
          <div className="flex gap-1.5">
            {[...BROKERS, "Other"].map((b) => (
              <button key={b} type="button" aria-pressed={broker === b} onClick={() => setBroker(b)}
                className={cn("flex-1 rounded-md border border-input px-3 py-1.5 text-sm", broker === b && "border-foreground bg-foreground text-background")}>
                {b}
              </button>
            ))}
          </div>
          {broker === "Other" && (
            <Input aria-label="Broker name" value={otherBroker} onChange={(e) => setOtherBroker(e.target.value)} placeholder="e.g. Upstox" maxLength={40} />
          )}
        </fieldset>

        <div className="space-y-2">
          <Label htmlFor="buy-date">Bought on <span className="font-normal text-muted-foreground">(optional)</span></Label>
          <Input id="buy-date" type="date" value={buyDate} onChange={(e) => setBuyDate(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="note">Note <span className="font-normal text-muted-foreground">(optional)</span></Label>
          <Textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} rows={2} maxLength={500} />
        </div>

        {error && <p role="alert" className="text-sm text-loss">{error}</p>}
      </div>

      <SheetFooter className="flex-row gap-2">
        {holding && (
          <Button type="button" variant="outline" onClick={del} disabled={remove.isPending} className="text-loss">
            {remove.isPending ? "Deleting…" : "Delete"}
          </Button>
        )}
        <Button type="submit" disabled={save.isPending} className="flex-1">
          {save.isPending ? "Saving…" : holding ? "Save changes" : "Add holding"}
        </Button>
      </SheetFooter>
    </form>
  );
}
