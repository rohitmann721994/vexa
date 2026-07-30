"""Authenticated API access that reuses a real browser login.

Many modern apps sit behind an SPA + OpenID Connect login with no server-side
HTML form, so there is no clean way to authenticate `requests` directly. This
library solves that: it logs in once via Playwright (a real browser), captures
the session cookies off a genuine authenticated request, and hands back an
authenticated ``requests.Session`` plus a ``get(endpoint)`` helper.

Cookie capture strategy (in priority order):

1. **Intercept the raw ``Cookie`` header** off the first authenticated request
   the app makes (via a Playwright request listener). This is the most robust
   method and works even when cookies are chunked/split by a BFF proxy — the
   browser sends exactly what the server expects.
2. **Fall back to ``context.cookies()``** re-serialized into a header. Simpler,
   but if your backend uses chunked BFF cookies (e.g. ``X-bff=chunks-2`` with
   the payload split across ``...C1``/``...C2``), the reassembled value may be
   rejected — see the note in ``_build_cookie_from_context``.

Captured cookies are de-duplicated (first occurrence wins — important for
load-balancer cookies like ``AWSALB``) and persisted to ``.env`` as a single
``API_COOKIES=`` line for reuse across runs.
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from pages.ui.login_page import LoginPage
from utils.logger import get_logger

load_dotenv()

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
# Path prefix that identifies an authenticated request whose Cookie header we
# want to steal. Override via API_COOKIE_TRIGGER (default: '/api/').
_COOKIE_TRIGGER = os.getenv("API_COOKIE_TRIGGER", "/api/")


class ApiLibrary:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = (base_url or os.getenv("API_BASE_URL", "")).rstrip("/")
        self._logger = get_logger(__name__)
        self._session: Optional[requests.Session] = None
        self._cookie_header: str = ""

    # -- public API ---------------------------------------------------------

    def login_and_get_cookies(self, ui_base_url: Optional[str] = None) -> str:
        """Drive a browser login and return the captured Cookie header string.
        Also persists it to .env as API_COOKIES and builds the session."""
        ui_url = ui_base_url or os.getenv("UI_BASE_URL", "")
        user = os.getenv("QA_USERNAME")
        pwd = os.getenv("QA_PASSWORD")
        if not (ui_url and user and pwd):
            raise RuntimeError("Need UI_BASE_URL, QA_USERNAME and QA_PASSWORD in .env to log in.")

        captured: Dict[str, str] = {"header": ""}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def _on_request(request):
                if not captured["header"] and _COOKIE_TRIGGER in request.url:
                    header = request.headers.get("cookie", "")
                    if header:
                        captured["header"] = header

            page.on("request", _on_request)

            login = LoginPage(page)
            login.open(ui_url)
            login.login_as(user, pwd)
            # Give the app a moment to fire its first authenticated request.
            page.wait_for_timeout(5000)

            cookie_header = captured["header"] or self._build_cookie_from_context(context)
            browser.close()

        cookie_header = self._dedupe_cookies(cookie_header)
        self._cookie_header = cookie_header
        self._persist_cookies(cookie_header)
        self._build_session(cookie_header)
        self._logger.info("Captured %d cookie(s) for API session", len(cookie_header.split(";")))
        return cookie_header

    def session(self) -> requests.Session:
        """Return the authenticated session, building it from .env if needed."""
        if self._session is not None:
            return self._session
        cookie_header = os.getenv("API_COOKIES", "")
        if cookie_header:
            self._build_session(cookie_header)
            return self._session
        # No cached cookies — perform a fresh login.
        self.login_and_get_cookies()
        return self._session

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET an endpoint (absolute or relative to API_BASE_URL) with full
        request/response logged for debugging."""
        url = endpoint if endpoint.startswith("http") else f"{self._base_url}/{endpoint.lstrip('/')}"
        self._logger.info("GET %s", url)
        resp = self.session().get(url, **kwargs)
        self._logger.debug("-> %s (%d bytes)", resp.status_code, len(resp.content))
        return resp

    # -- internals ----------------------------------------------------------

    def _build_session(self, cookie_header: str) -> None:
        s = requests.Session()
        s.headers.update({"Cookie": cookie_header, "Accept": "application/json"})
        self._session = s

    @staticmethod
    def _dedupe_cookies(cookie_header: str) -> str:
        """Keep the first occurrence of each cookie name (matters for LB cookies)."""
        seen = set()
        out = []
        for part in cookie_header.split(";"):
            part = part.strip()
            if not part:
                continue
            name = part.split("=", 1)[0].strip()
            if name in seen:
                continue
            seen.add(name)
            out.append(part)
        return "; ".join(out)

    @staticmethod
    def _build_cookie_from_context(context) -> str:
        """Fallback: serialize context cookies into a header.

        NOTE: If your backend uses chunked BFF cookies (a marker cookie like
        ``X-bff=chunks-N`` plus ``...C1``/``...C2`` payload chunks), do NOT let
        the reassembled single value through — re-emit the ``chunks-N`` marker
        form the browser actually sent. The interception path above avoids this
        problem entirely, which is why it is preferred.
        """
        parts = [f"{c['name']}={c['value']}" for c in context.cookies()]
        return "; ".join(parts)

    def _persist_cookies(self, cookie_header: str) -> None:
        """Write/replace the single API_COOKIES= line in .env."""
        line = f"API_COOKIES={cookie_header}\n"
        if _ENV_PATH.exists():
            text = _ENV_PATH.read_text(encoding="utf-8")
            if re.search(r"^API_COOKIES=.*$", text, flags=re.MULTILINE):
                text = re.sub(r"^API_COOKIES=.*$", line.rstrip("\n"), text, flags=re.MULTILINE)
            else:
                text = text.rstrip("\n") + "\n" + line
            _ENV_PATH.write_text(text, encoding="utf-8")
        else:
            _ENV_PATH.write_text(line, encoding="utf-8")
