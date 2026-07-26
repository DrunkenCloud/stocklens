"""Breeze session auth, isolated here so the rest of the pipeline never sees it.

Session flow (see ../03_PIPELINE.md):
  1. One-time: register an app in the ICICI Breeze developer portal -> api_key, api_secret.
  2. Per session: visit login_url(), log in, copy the session token from the
     redirect URL into BREEZE_API_SESSION. It expires periodically (not permanent) -
     for v1 this is a manual refresh; automating it is a later convenience, not a
     dependency (03_PIPELINE.md).
"""
import os
from urllib.parse import quote

from breeze_connect import BreezeConnect


def login_url() -> str:
    api_key = os.environ["BREEZE_API_KEY"]
    return f"https://api.icicidirect.com/apiuser/login?api_key={quote(api_key)}"


def get_client() -> BreezeConnect:
    api_key = os.environ["BREEZE_API_KEY"]
    api_secret = os.environ["BREEZE_API_SECRET"]
    session_token = os.environ["BREEZE_API_SESSION"]

    client = BreezeConnect(api_key=api_key)
    client.generate_session(api_secret=api_secret, session_token=session_token)
    return client
