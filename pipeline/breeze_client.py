import os
from urllib.parse import quote

from breeze_connect import BreezeConnect

from pipeline.db import connect


class SessionExpired(Exception):
    pass


def is_session_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(s in msg for s in ("session key is expired", "invalid session", "please check session key"))


def login_url() -> str:
    return f"https://api.icicidirect.com/apiuser/login?api_key={quote(os.environ['BREEZE_API_KEY'])}"


def mark_session_invalid() -> None:
    with connect() as conn:
        conn.execute("UPDATE breeze_session SET invalid_at = now() WHERE invalid_at IS NULL")


def check_response(resp: dict) -> list:
    success = resp.get("Success") if isinstance(resp, dict) else None
    if isinstance(success, list):
        return success
    error = resp.get("Error") if isinstance(resp, dict) else resp
    if success is None and not error:
        return []
    err = RuntimeError(f"Breeze error: {error}")
    if is_session_error(err):
        mark_session_invalid()
        raise SessionExpired(str(error)) from err
    raise err


def get_client() -> BreezeConnect:
    with connect() as conn:
        row = conn.execute("SELECT token FROM breeze_session WHERE id = 1 AND invalid_at IS NULL").fetchone()
    if row is None:
        raise SessionExpired("no valid Breeze session")

    client = BreezeConnect(api_key=os.environ["BREEZE_API_KEY"])
    try:
        client.generate_session(api_secret=os.environ["BREEZE_API_SECRET"], session_token=row[0])
    except Exception as e:
        if is_session_error(e):
            mark_session_invalid()
            raise SessionExpired(str(e)) from e
        raise
    return client
