"""Captures the Breeze session token from the login redirect instead of
requiring manual copy-paste into .env. See pipeline/README.md and
06_DECISIONS.md D10.

The redirect target is a fixed setting in the user's Breeze app registration
on ICICI's developer portal (not passed dynamically), so it must be
registered there as:
    https://<domain>/api/breeze/callback/<BREEZE_CALLBACK_TOKEN>
The path-embedded token is the only guard on this endpoint (no other auth in
this single-user app) - a wrong/missing token gets a 404, not a 401/403, so
the endpoint's existence isn't advertised to random scanners.
"""
import os
import pathlib
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Response

router = APIRouter()


@router.get("/breeze/login-url")
def breeze_login_url():
    # Mirrors pipeline/breeze_client.py's login_url() - duplicated rather than
    # imported since backend/ and pipeline/ are deliberately separate
    # (01_ARCHITECTURE.md: pipeline is "not imported by API"). api_key alone
    # can't authenticate anything (needs api_secret + a real login too), so
    # exposing it here is no riskier than an OAuth client_id.
    api_key = os.environ["BREEZE_API_KEY"]
    return {"url": f"https://api.icicidirect.com/apiuser/login?api_key={quote(api_key)}"}


def env_file_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get("ENV_FILE_PATH", "../.env"))


def set_env_var(path: pathlib.Path, key: str, value: str) -> None:
    lines = path.read_text().splitlines() if path.exists() else []
    prefix = f"{key}="
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{prefix}{value}"
            path.write_text("\n".join(lines) + "\n")
            return
    lines.append(f"{prefix}{value}")
    path.write_text("\n".join(lines) + "\n")


@router.get("/breeze/callback/{token}")
def breeze_callback(token: str, apisession: str):
    expected = os.environ.get("BREEZE_CALLBACK_TOKEN")
    if not expected or token != expected:
        raise HTTPException(status_code=404, detail="not found")

    set_env_var(env_file_path(), "BREEZE_API_SESSION", apisession)

    return Response(
        content="<html><body><h1>Breeze session captured</h1><p>You can close this tab.</p></body></html>",
        media_type="text/html",
    )
