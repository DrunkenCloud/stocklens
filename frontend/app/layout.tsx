export const metadata = {
  title: "StockLens",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <nav style={{ padding: "12px 24px", borderBottom: "1px solid #eee", fontFamily: "system-ui, sans-serif" }}>
          <a href="/" style={{ marginRight: 16 }}>Screener</a>
          <a href="/portfolio">Portfolio</a>
        </nav>
        {children}
      </body>
    </html>
  );
}
