from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import pool
from routers import admin, breeze_auth, portfolio, prices, screen, stocks

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


@app.get("/api/health")
def health():
    with pool.connection() as conn:
        (count,) = conn.execute("SELECT count(*) FROM companies").fetchone()
    return {"status": "ok", "companies": count}
