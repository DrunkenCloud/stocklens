from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import pool
from routers import prices, screen, stocks

app = FastAPI(title="StockLens API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(prices.router)
app.include_router(stocks.router)
app.include_router(screen.router)


@app.get("/health")
def health():
    with pool.connection() as conn:
        (count,) = conn.execute("SELECT count(*) FROM companies").fetchone()
    return {"status": "ok", "companies": count}
