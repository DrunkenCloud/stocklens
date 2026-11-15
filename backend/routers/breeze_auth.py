import os
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from db import pool
from jobs import JobAlreadyRunning, spawn_job

router = APIRouter()


@router.get("/breeze/login-url")
def breeze_login_url():
    return {"url": f"https://api.icicidirect.com/apiuser/login?api_key={quote(os.environ['BREEZE_API_KEY'])}"}


@router.api_route("/cb/{token}", methods=["GET", "POST"])
async def breeze_callback(token: str, request: Request):
    expected = os.environ.get("BREEZE_CALLBACK_TOKEN")
    if not expected or token != expected:
        raise HTTPException(status_code=404, detail="not found")

    apisession = request.query_params.get("apisession")
    if not apisession and request.method == "POST":
        apisession = (await request.form()).get("apisession")
    if not apisession:
        raise HTTPException(status_code=400, detail="missing apisession")

    with pool.connection() as conn:
        conn.execute(
            """
            INSERT INTO breeze_session (id, token, captured_at, invalid_at) VALUES (1, %s, now(), NULL)
            ON CONFLICT (id) DO UPDATE SET token = EXCLUDED.token, captured_at = now(), invalid_at = NULL
            """,
            (apisession,),
        )
    try:
        spawn_job("sync_icici", trigger="auto")
    except JobAlreadyRunning:
        pass

    return HTMLResponse(
        '<!doctype html><meta http-equiv="refresh" content="1;url=/">'
        "<body style=\"font-family:system-ui;padding:2rem\">ICICI connected - updating prices. "
        'Taking you back to <a href="/">StockLens</a>…</body>'
    )
