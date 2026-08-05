---
name: write-api-test
description: Use when adding a new API test to this Vexa repo — a JSON/HTTP endpoint test that authenticates by reusing a real browser login via ApiLibrary. Triggers include "write an API test for X", "add a test for this endpoint", "test the /api/... route", "verify this endpoint returns Y".
---

# Write an API Test

## Overview

Scaffold a new API test the way this framework expects: authenticate once
through a real browser login (Playwright captures the session cookies), then hit
JSON endpoints with an authenticated `requests.Session`. Read `CLAUDE.md` first
— especially the **Authentication flow** section, which explains why login goes
through a browser and how cookies are captured.

## Why it works this way

The app sits behind an SPA + SSO login with no server-side form, so `requests`
can't log in directly. `ApiLibrary` drives a browser login once per session,
intercepts the raw `Cookie` header off the app's first authenticated request
(keyed on `API_COOKIE_TRIGGER`, default `/api/`), and hands you an authenticated
session. Tests just call `api_library.get(endpoint)`.

## Steps

Track these as todos; do them in order.

### 1. Confirm the endpoint and expected shape

Hit the endpoint in the browser (or via the app's network tab) while logged in.
Note the path, the expected status, and the JSON shape you'll assert on. Confirm
whether it needs query params or a specific account/role.

### 2. Set config in `.env`

- `API_BASE_URL` — base for JSON endpoints (often the UI origin + `/api`).
- `UI_BASE_URL`, `QA_USERNAME`, `QA_PASSWORD` — used for the one-time browser login.
- `API_COOKIE_TRIGGER` — override if the app's authenticated requests don't hit
  `/api/` (e.g. `/gateway/`).

### 3. Write the test

`tests/api/test_<feature>.py`. Follow `tests/api/test_example_api.py`:

```python
import pytest


@pytest.mark.api
def test_orders_endpoint_returns_list(api_library):
    resp = api_library.get("orders?status=open")
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:500]}"
    data = resp.json()
    assert isinstance(data, list), f"expected a list, got {type(data).__name__}"
    assert all("id" in o for o in data), "every order should carry an id"
```

Requirements:
- `@pytest.mark.api` (register any new marker in `pytest.ini` first —
  `--strict-markers` is on).
- Use the `api_library` fixture (session-scoped: logs in once per run) or
  `api_session` for the raw `requests.Session`.
- Assertion messages print the status and a slice of the body so failures are
  self-explanatory.
- Guard on config with a module-level `skipif` when the test can't run without
  a configured app, so a fresh clone stays green (see the example).

### 4. Run it

```bash
uv run pytest tests/api/test_<feature>.py -m api
```

If cookies expire mid-run, delete the `API_COOKIES=` line from `.env` (or call
`api_library.login_and_get_cookies()`) to force a fresh login. Report the actual
outcome; never claim a PASS you didn't get.

## Common Mistakes

- Building a `requests.Session` by hand instead of using `ApiLibrary` — you'll
  fight the SSO login and (if the backend chunks BFF cookies) get rejected auth.
- Reassembling `context.cookies()` into a header for a chunked-BFF backend — the
  server rejects the reassembled value. Let `ApiLibrary` intercept the raw header.
- Asserting only the status code — assert the response shape too.
- Unregistered marker (fails under `--strict-markers`).
