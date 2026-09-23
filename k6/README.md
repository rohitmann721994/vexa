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
  scripts/          smoke-test.js, load-test.js, stress-test.js, spike-test.js, soak-test.js
  scenarios/        api-scenarios.js — template for multi-endpoint coverage
  utils/            auth.js (reuses ApiLibrary's captured cookie), report.js (per-run HTML+JSON)
  thresholds/       default-thresholds.js — shared pass/fail criteria
  config/           environments.js — resolves BASE_URL from env
  data/             CSV/JSON fixtures for data-driven scripts (SharedArray)
  report_template/  perf_summary_template.html + narrative.example.json — the
                     executive "results at a glance" summary (see below)
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
writes to, already gitignored. That's the technical, per-run report.

## Executive summary report ("results at a glance")

For handing results to a ticket/leadership rather than another QA, build the
tile-grid summary report (load/stress/spike/soak side by side, click a tile
for the detail, signed off at the bottom) from the JSON files the runs above
already produced:

```bash
cp k6/report_template/narrative.example.json k6/report_template/narrative.json
# edit narrative.json: verdict headline/sub, secondary findings, recommendations

uv run python utils/perf_summary.py \
  --load    reports/k6_load_<timestamp>.json \
  --stress  reports/k6_stress_<timestamp>.json \
  --spike   reports/k6_spike_<timestamp>.json \
  --soak    reports/k6_soak_<timestamp>.json \
  --narrative k6/report_template/narrative.json
```

Omit any `--load`/`--stress`/`--spike`/`--soak` flag and it picks the most
recent matching `reports/k6_<type>_*.json` automatically. The pass/warn/fail
pill, p95, concurrency, and request counts come straight from the JSON — only
the headline verdict, findings, and recommendations are written by a person.
The signoff defaults to `Rohit Mann` / `Catalis QA`; override with
`--prepared-by` / `--prepared-by-role` (or set them in `narrative.json`) if
someone else is running it. Output: `reports/perf_summary_<timestamp>.html`.

See the vendored [`k6-performance`](../.claude/skills/k6-performance/SKILL.md)
skill for general k6 authoring patterns, and
[`write-performance-test`](../.claude/skills/write-performance-test/SKILL.md)
for how to scaffold a new script against a real endpoint in this repo.
