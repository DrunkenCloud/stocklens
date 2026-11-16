"use client";

import { ChartNoAxesColumnIcon, LayersIcon, MoonIcon, ReceiptIndianRupeeIcon, SettingsIcon, SunIcon, WalletIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";

import { StatusBanner } from "@/components/status-banner";
import { StockSearch } from "@/components/stock-search";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Holdings", icon: WalletIcon },
  { href: "/exposure", label: "Exposure", icon: LayersIcon },
  { href: "/tax", label: "Tax", icon: ReceiptIndianRupeeIcon },
  { href: "/screener", label: "Screener", icon: ChartNoAxesColumnIcon },
  { href: "/admin", label: "Data", icon: SettingsIcon },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const active = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4">
          <Link href="/" className="font-heading text-lg font-semibold tracking-tight">
            StockLens
          </Link>
          <nav className="ml-4 hidden items-center gap-1 md:flex" aria-label="Main">
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                aria-current={active(n.href) ? "page" : undefined}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground",
                  active(n.href) && "bg-secondary text-foreground",
                )}
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <StockSearch className="ml-auto w-9 justify-center px-0 sm:w-64 sm:justify-start sm:px-3 lg:w-80" />
          <ThemeToggle />
        </div>
      </header>
      <StatusBanner />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 pt-6 pb-24 md:pb-12">{children}</main>
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-border bg-background/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
      >
        {NAV.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            aria-current={active(n.href) ? "page" : undefined}
            className={cn("flex flex-col items-center gap-0.5 py-2 text-xs text-muted-foreground", active(n.href) && "text-foreground")}
          >
            <n.icon className="size-5" aria-hidden />
            {n.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  return (
    <button
      type="button"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      className="grid size-9 place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground"
      aria-label="Toggle dark mode"
    >
      <SunIcon className="hidden size-4 dark:block" />
      <MoonIcon className="size-4 dark:hidden" />
    </button>
  );
}
