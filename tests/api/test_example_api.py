"""Example API test — a template to copy, and a live check.

Uses the session-scoped ``api_library`` fixture (browser login once → cookie
capture → authenticated ``requests.Session``) to hit a JSON endpoint. On a
fresh clone with the API/login env vars unset it SKIPS cleanly, so
``uv run pytest`` stays green out of the box.

Configure ``API_BASE_URL``, ``UI_BASE_URL``, ``QA_USERNAME`` and ``QA_PASSWORD``
in ``.env`` (and set ``API_ENDPOINT`` below or via env) to make it run.
"""

import os

import pytest

_REQUIRED = ("API_BASE_URL", "UI_BASE_URL", "QA_USERNAME", "QA_PASSWORD")

pytestmark = pytest.mark.skipif(
    not all(os.getenv(v) for v in _REQUIRED),
    reason=f"API test needs {', '.join(_REQUIRED)} in .env.",
)


@pytest.mark.api
def test_endpoint_returns_ok(api_library):
    # Point this at a known-good authenticated endpoint for your app.
    endpoint = os.getenv("API_ENDPOINT", "")
    if not endpoint:
        pytest.skip("Set API_ENDPOINT to a JSON endpoint to exercise this test.")

    resp = api_library.get(endpoint)
    assert resp.status_code == 200, (
        f"GET {endpoint} -> {resp.status_code}\n{resp.text[:500]}"
    )
