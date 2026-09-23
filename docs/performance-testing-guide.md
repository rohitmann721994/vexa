# Performance Testing Guide (k6)

Vexa's UI/API suites answer "does it work?"; this module answers "does it
work **under load**, and where does it break?" It's built with
[k6](https://k6.io/) and layered on top of the same authenticated session
`ApiLibrary` already captures for `tests/api/`.

## Prerequisites

- **The k6 binary** — a separate install from Python/`uv`. See
  https://k6.io/docs/get-started/installation/. `uv sync` does **not**
  install it, and `k6 run` is invoked directly, not through `pytest`.
- A configured `.env` (`UI_BASE_URL`, `QA_USERNAME`, `QA_PASSWORD`,
  `API_BASE_URL`) — same as the rest of the framework.

## Authentication: reuse, don't reinvent

The app is an SPA behind OpenID Connect / SSO with no server-side login
form (see `CLAUDE.md` → "Authentication flow"). k6 has no browser, so it
**cannot log in on its own**. Instead it replays the raw `Cookie` header
`ApiLibrary` already captured:

```bash
# One-time (or whenever the cookie expires): mint/refresh API_COOKIES in .env.
uv run pytest tests/api/test_example_api.py -m api
```

Then export the same two values k6 needs (`.env` isn't read by k6 directly):

**bash / Git Bash:**
```bash
export API_BASE_URL=$(grep -m1 ^API_BASE_URL .env | cut -d= -f2-)
export API_COOKIES=$(grep -m1 ^API_COOKIES .env | cut -d= -f2-)
```

**PowerShell:**
```powershell
$env:API_BASE_URL = (Select-String '^API_BASE_URL=(.*)' .env).Matches[0].Groups[1].Value
$env:API_COOKIES  = (Select-String '^API_COOKIES=(.*)'  .env).Matches[0].Groups[1].Value
```

If a run starts seeing 401s or redirects to the login page, the cookie
expired — re-run the capture step above and re-export before continuing.
For long soak tests, check the app's SSO session TTL before scheduling —
the cookie may not outlive a multi-hour run.

## Types of testing

| Type | Question it answers | Typical shape | Script |
|------|---------------------|----------------|--------|
| **Smoke** | Does the endpoint work at all? | 1 VU, 1 minute | `k6/scripts/smoke-test.js` |
| **Load** | Does it meet its SLA at expected steady-state traffic? | Ramp to expected concurrency, hold | `k6/scripts/load-test.js` |
| **Stress** | Where's the breaking point, and how does it degrade? | Step up well past expected load | `k6/scripts/stress-test.js` |
| **Spike** | Does it survive a sudden burst, and recover after? | Short, sharp burst then drop | `k6/scripts/spike-test.js` |
| **Soak** | Does anything degrade over hours (leaks, pool exhaustion, disk growth)? | Moderate load, sustained for hours | `k6/scripts/soak-test.js` |

Run order: **smoke → load → stress/spike → soak.** If smoke fails, the
others will fail for the same reason at a much higher time cost.

## Generic info required before running

- `API_BASE_URL` / `API_COOKIES` exported (see above).
- `K6_ENV` (optional) — label for which target you're hitting
  (`local`/`staging`/`prod`); defaults to `local`. Never run stress/spike/soak
  against a shared staging or production environment without telling the
  team first.
- Thresholds — every script defines pass/fail criteria upfront
  (`k6/thresholds/default-thresholds.js`); a run with no thresholds is an
  observation, not a test.
- Realistic think time (`sleep()`) between requests — instant hammering
  isn't representative of real traffic.

## Report style

Matches the convention `conftest.py` already uses for the pytest suite: one
timestamped, self-contained file per run, written to the shared `reports/`
folder (already gitignored):

- `reports/k6_<test>_<timestamp>.html` — self-contained HTML summary (via
  the `k6-reporter` library), open directly in a browser, same spirit as
  `reports/report_<timestamp>.html` from the UI/API suites.
- `reports/k6_<test>_<timestamp>.json` — raw metrics, for trend analysis or
  CI parsing across runs.
- A text summary also prints to stdout for a quick pass/fail glance.

This comes from every script's `handleSummary` export
(`k6/utils/report.js:handleSummaryReport`) — don't drop it when writing a
new script, or the run won't produce the standard report.

### Executive summary report

The per-run HTML/JSON above is a technical report — the one to hand to a
ticket or leadership is a separate tile-grid summary (load/stress/spike/soak
side by side, click a tile for the full detail, signed off at the bottom):
`utils/perf_summary.py` builds it from the JSON files the runs already wrote.

```bash
cp k6/report_template/narrative.example.json k6/report_template/narrative.json
# edit narrative.json — verdict headline/sub, findings, recommendations

uv run python utils/perf_summary.py \
  --load reports/k6_load_<ts>.json --stress reports/k6_stress_<ts>.json \
  --spike reports/k6_spike_<ts>.json --soak reports/k6_soak_<ts>.json \
  --narrative k6/report_template/narrative.json
```

The pill (pass/watch/fail), p95, concurrency, and request counts are computed
from the JSON; the verdict headline, findings, and recommendations are
written by whoever ran the test — this script won't fabricate those.
Signoff defaults to `Rohit Mann` / `Catalis QA`; override with
`--prepared-by`/`--prepared-by-role` if someone else runs it. Output:
`reports/perf_summary_<timestamp>.html`.

## Running

```bash
k6 run k6/scripts/smoke-test.js
k6 run k6/scripts/load-test.js
k6 run k6/scripts/stress-test.js
k6 run k6/scripts/spike-test.js
k6 run k6/scripts/soak-test.js          # hours long — run deliberately
k6 run k6/scenarios/api-scenarios.js    # multi-endpoint template

# Override VUs/duration for a quick check without editing the script:
k6 run --vus 10 --duration 30s k6/scripts/smoke-test.js
```

## Where to look next

- [`k6/README.md`](../k6/README.md) — module layout and quick start.
- [`.claude/skills/write-performance-test/SKILL.md`](../.claude/skills/write-performance-test/SKILL.md)
  — scaffold a new script against a real endpoint in this repo.
- [`.claude/skills/k6-performance/SKILL.md`](../.claude/skills/k6-performance/SKILL.md)
  — general k6 syntax: executors, custom metrics, data-driven tests,
  best-practices/anti-patterns.

## CI note

Performance tests are **not** wired into the GitHub Actions workflow that
runs on every push/PR — load/stress/spike/soak runs against a shared
environment need explicit scheduling and team awareness, not a per-commit
trigger. Run them manually, or wire a dedicated scheduled workflow if your
team wants recurring runs.
