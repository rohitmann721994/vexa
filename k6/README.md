# Vexa Performance Module (k6)

Load/stress/spike/soak testing for the app under test, layered on top of the
same authenticated session the `tests/api/` suite already uses. Full guide:
[docs/performance-testing-guide.md](../docs/performance-testing-guide.md).

k6 is a **separate toolchain** from the Python/`uv` side of this repo — it is
not installed by `uv sync` and does not run through `pytest`. Install the k6
binary yourself: https://k6.io/docs/get-started/installation/.

## Layout

```
k6/
  scripts/       smoke-test.js, load-test.js, stress-test.js, spike-test.js, soak-test.js
  scenarios/     api-scenarios.js — template for multi-endpoint coverage
  utils/         auth.js (reuses ApiLibrary's captured cookie), report.js (HTML+JSON report)
  thresholds/    default-thresholds.js — shared pass/fail criteria
  config/        environments.js — resolves BASE_URL from env
  data/          CSV/JSON fixtures for data-driven scripts (SharedArray)
```

## Quick start

```bash
# 1. One-time: capture an authenticated cookie the same way ApiLibrary does.
uv run pytest tests/api/test_example_api.py -m api

# 2. Export the same values k6 needs (bash example — see the full guide for
#    PowerShell). These already live in .env.
export API_BASE_URL=$(grep -m1 ^API_BASE_URL .env | cut -d= -f2-)
export API_COOKIES=$(grep -m1 ^API_COOKIES .env | cut -d= -f2-)

# 3. Run a smoke test first, always.
k6 run k6/scripts/smoke-test.js

# 4. Then load/stress/spike/soak as needed.
k6 run k6/scripts/load-test.js
```

Every script writes a self-contained HTML report plus raw JSON to
`reports/k6_<test>_<timestamp>.*` — the same `reports/` folder pytest-html
writes to, already gitignored.

See the vendored [`k6-performance`](../.claude/skills/k6-performance/SKILL.md)
skill for general k6 authoring patterns, and
[`write-performance-test`](../.claude/skills/write-performance-test/SKILL.md)
for how to scaffold a new script against a real endpoint in this repo.
