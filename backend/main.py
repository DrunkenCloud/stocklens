from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import pool
from routers import admin, breeze_auth, mf, portfolio, prices, screen, securities, status, stocks, tax

app = FastAPI(title="StockLens API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(prices.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(screen.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(breeze_auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(securities.router, prefix="/api")
app.include_router(mf.router, prefix="/api")
app.include_router(tax.router, prefix="/api")


@app.get("/api/health")
def health():
    with pool.connection() as conn:
        count = conn.execute("SELECT count(*) AS n FROM companies").fetchone()["n"]
    return {"status": "ok", "companies": count}
