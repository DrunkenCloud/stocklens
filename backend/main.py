from fastapi import FastAPI

from db import pool

app = FastAPI(title="StockLens API")


@app.get("/health")
def health():
    with pool.connection() as conn:
        (count,) = conn.execute("SELECT count(*) FROM companies").fetchone()
    return {"status": "ok", "companies": count}
