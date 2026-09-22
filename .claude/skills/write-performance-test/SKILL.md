---
name: write-performance-test
description: Use when adding a new k6 performance test to this Vexa repo — load/stress/spike/soak/smoke testing an endpoint using the app's already-authenticated session. Triggers include "write a performance test for X", "load test this endpoint", "add a k6 script for X", "stress test the app", "how many users can this endpoint handle".
---

# Write a Performance Test

## Overview

Scaffold a new k6 script the way this framework expects: under `k6/scripts/`
or `k6/scenarios/`, reusing the same session cookie `ApiLibrary` already
captures (`k6/utils/auth.js`), with thresholds defined upfront and a report
written to `reports/` in the same self-contained-HTML style as the pytest
suite. Read `docs/performance-testing-guide.md` first for the full reference
(test types, thresholds, report format); read the vendored `k6-performance`
skill for generic k6 syntax (executors, custom metrics, data-driven tests).

**k6 is a separate toolchain.** It is not installed by `uv sync` and does not
run through `pytest` — it needs the k6 binary installed separately and is
invoked directly with `k6 run`.

## Why auth works differently here

The app is an SPA + SSO with no server-side login form (see CLAUDE.md's
"Authentication flow" section) — the same reason `ApiLibrary` exists for the
`tests/api/` suite. k6 has no browser, so it **cannot** log in on its own; it
replays the raw `Cookie` header `ApiLibrary` already captured into
`API_COOKIES` in `.env`. Never write a k6 script that tries to POST credentials
to a login endpoint directly — that's not how this app authenticates.

## Steps

Track these as todos; do them in order.

### 1. Pick the test type

| Type | Question it answers | Script |
|------|---------------------|--------|
| Smoke | Does it work at all, at minimal load? | `k6/scripts/smoke-test.js` |
| Load | Does it meet its SLA at expected steady-state traffic? | `k6/scripts/load-test.js` |
| Stress | Where's the breaking point, and how does it degrade? | `k6/scripts/stress-test.js` |
| Spike | Does it survive a sudden burst, and recover? | `k6/scripts/spike-test.js` |
| Soak | Does anything degrade over hours (leaks, exhaustion)? | `k6/scripts/soak-test.js` |

Always run smoke first — if it fails, load/stress/spike/soak will fail for
the same reason at much higher cost.

### 2. Confirm the endpoint

Same discipline as `write-api-test`: hit the endpoint in the browser or via
`tests/api/` while logged in. Note the path, expected status, and whether it
needs query params or a specific role.

### 3. Make sure auth is available

```bash
uv run pytest tests/api/test_example_api.py -m api   # mints/refreshes API_COOKIES
```

Then export `API_BASE_URL` and `API_COOKIES` from `.env` into the shell (k6
reads `__ENV`, not `.env` files — see `docs/performance-testing-guide.md` for
the exact one-liners for bash and PowerShell).

### 4. Write or extend the script

For a single endpoint, copy the relevant `k6/scripts/*.js` and change the
request. For multiple endpoints in one run, copy `k6/scenarios/api-scenarios.js`
and add one `exec` function per flow. Always:

- Import `BASE_URL` from `k6/config/environments.js` and `authHeaders()` from
  `k6/utils/auth.js` — never hardcode the URL or rebuild the cookie by hand.
- Define `thresholds` (import from `k6/thresholds/default-thresholds.js` or
  set tighter ones for a specific SLA) — a script with no thresholds is just
  an observation, not a test.
- `check()` the response status/shape, not just that a request completed.
- Export `handleSummary` calling `handleSummaryReport('<name>', data)` from
  `k6/utils/report.js` so the run produces the standard HTML+JSON report.

### 5. Run it

```bash
k6 run k6/scripts/<name>-test.js
```

Reports land at `reports/k6_<name>_<timestamp>.html` (open in a browser) and
`.json` (raw metrics). Report the actual thresholds pass/fail k6 prints —
never claim a passing run you didn't see.

## Common Mistakes

- Trying to `http.post` a login/credentials request — this app can't
  authenticate that way; reuse `authHeaders()` instead.
- No thresholds, or thresholds copy-pasted without adjusting for the
  endpoint's real SLA.
- No think time (`sleep()`) between requests — instant hammering isn't a
  realistic traffic pattern.
- Running stress/spike/soak against a shared staging/prod environment without
  telling the team first (see the k6-performance skill's anti-patterns list).
- Forgetting `handleSummary` — without it, the run doesn't produce the
  standard `reports/` output the rest of the suite uses.
