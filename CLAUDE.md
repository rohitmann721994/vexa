# CLAUDE.md

Guidance for Claude Code (and any AI assistant) working in this repository.

> **Vexa** was created and authored by **Rohit Mann** (framework design,
> architecture, and AI-assistant rules/skills). Maintained by Catalis QA.

## Overview

**Vexa** is a reusable test-automation framework for Catalis QA teams. It drives
web apps that sit behind an SPA + OpenID Connect / SSO login, where there is no
server-side HTML form — so login must go through a real browser (Playwright).
Two flavors of tests share one browser-login mechanism:

- **UI tests** drive the browser directly with Playwright.
- **API tests** reuse the browser login to capture session cookies, then hit
  JSON endpoints with `requests`.

Stack: `uv` (deps + pinned Python 3.14, see `requires-python = "==3.14.*"` in
`pyproject.toml`), `pytest`, `playwright`, `requests`, `pytest-html`.

> Adapting this framework to your app? Start with
> [docs/framework-setup-guide.md](docs/framework-setup-guide.md).

## Commands

```bash
uv sync                       # install/resolve dependencies (incl. dev group)
uv run playwright install     # install browser binaries (chromium) — required once
uv run pytest                 # run full suite; writes timestamped HTML report to reports/
uv run pytest -m ui           # only UI tests
uv run pytest -m api          # only API tests
uv run pytest -m smoke        # only smoke tests
uv run pytest tests/ui/test_example_login.py::test_login_reaches_app  # single test
uv run pytest -n auto         # parallel (pytest-xdist)

k6 run k6/scripts/smoke-test.js   # performance tests — separate toolchain, see below
```

There is no separate build or lint step — this is a test-only repo. Use `uv`,
never `pip` directly.

## Architecture

Layered, with strict separation between test logic, reusable "library" facades,
and page objects. **Keep these boundaries** — they are the whole point of the
framework.

- **`tests/`** — pytest functions ONLY. No locators, no raw Playwright calls.
  UI tests use the `uiLibrary` fixture; API tests use `api_library` /
  `api_session`. Every test carries a marker (`ui` / `api` / `smoke` / ...).
- **`libraries/`** — high-level facades tests call:
  - `UiLibrary` — Playwright lifecycle (`open_application` / `close_application`),
    login, and navigation. Reads `UI_BASE_URL` and `QA_USERNAME`/`QA_PASSWORD`
    from `.env`. Browser engine selectable via `VEXA_BROWSER`.
  - `ApiLibrary` — logs in via Playwright, captures cookies, exposes an
    authenticated `requests.Session` plus a `get(endpoint)` helper.
- **`pages/ui/`** — Page Object Model. Locators + page actions live here
  (`LoginPage`, `HomePage`). No assertions in page objects.
- **`utils/`** — `logger.get_logger(name)` (console + `logs/automation.log`) and
  `evidence.Evidence` (annotated screenshots + `steps.md` proof).

### conftest hierarchy (fixtures cascade by directory)

- **`conftest.py`** (root) — timestamped `reports/report_<ts>.html`;
  screenshot-on-failure hook (fires for a Playwright `page` or a legacy `driver`
  funcarg).
- **`tests/conftest.py`** — `uiLibrary` fixture: function-scoped, auto-closes
  the browser on teardown.
- **`tests/api/conftest.py`** — `api_library` (session-scoped, logs in once) and
  `api_session`, so API login happens a single time per run.
- **`tests/ui/conftest.py`** — `evidence` fixture: per-test recorder, nests under
  the `@pytest.mark.ticket("ABC-123")` id when present.

### Authentication flow (the tricky part)

Because the app is an SPA behind SSO, login **must** go through a real browser
(Playwright). `ApiLibrary.login_and_get_cookies()` logs in, then **intercepts the
raw `Cookie` header** off the first authenticated request (a `page.on("request")`
listener keyed on `API_COOKIE_TRIGGER`, default `/api/`), falling back to
re-serializing `context.cookies()` only if interception fails. Cookies are
de-duplicated (first occurrence wins — matters for load-balancer cookies like
`AWSALB`) and persisted to `.env` as a single `API_COOKIES=` line.

> If your backend uses **chunked BFF cookies** (a marker cookie `X-bff=chunks-N`
> plus `...C1`/`...C2` payload chunks), the reassembled single value is rejected
> by the server. The interception path avoids this; the fallback documents it.
> Preserve the chunked form and the dedup behavior or API auth will start failing.

## Conventions

- **Markers** are registered in `pytest.ini` and `--strict-markers` is on — add a
  marker there before using it. Tag verification tests with
  `@pytest.mark.ticket("ABC-123")`.
- **Test discovery**: files must be named `test_*.py`, functions `test_*`. A file
  that doesn't match won't be collected even if it contains tests.
- **Logging**: use `get_logger(__name__)`, never `print()`.
- **Page objects hold locators + actions; tests hold assertions.** `UiLibrary`
  methods are high-level orchestration that delegate to page objects.
- **Evidence**: prefer `evidence.annotated_step(...)` for verification proof — it
  captures the step text, the expected result, and a red outline on the element
  under test. Use `image_step(...)` for off-screen content (downloaded PDF/docx
  rendered to PNG).

## Configuration

- **Credentials & URLs** come from `.env` (copy from `.env.example`). `.env` is
  **gitignored** — never commit real secrets or captured `API_COOKIES`.
- **`pytest.ini`** sets `pythonpath = . libraries`, `testpaths = tests`, live
  console logging (INFO) + file logging to `logs/automation.log` (DEBUG).
- **`reports/` and `logs/` are gitignored** — reports won't show in `git status`.

## Performance testing (k6)

`k6/` is a separate performance-testing module (smoke/load/stress/spike/soak)
covered in [docs/performance-testing-guide.md](docs/performance-testing-guide.md).
It's a **different toolchain** — the k6 binary, not `uv`/`pytest` — but reuses
the same authenticated session `ApiLibrary` captures: k6 has no browser, so it
replays the `Cookie` header from `API_COOKIES` in `.env` rather than logging
in itself. Reports follow the same self-contained-HTML convention as the
pytest suite, written to `reports/` as `k6_<test>_<timestamp>.html`/`.json`.
`utils/perf_summary.py` turns those JSON files into a separate executive
"results at a glance" tile-grid report (`reports/perf_summary_<timestamp>.html`),
signed off as `Rohit Mann` / `Catalis QA` by default.

## Versioning

**Every PR merged to `main` is a version bump** — Vexa follows
[SemVer](https://semver.org/), tracked in `VERSION` (mirrored into
`pyproject.toml`'s `version` field) and logged in `CHANGELOG.md`.
`.github/workflows/version-on-merge.yml` does this automatically on merge —
you don't bump it by hand in a PR:

- PR title/body has `BREAKING CHANGE` or a title ending `!` → **major**.
- PR title starts with `feat`/`add`/`feature` → **minor**.
- Everything else → **patch** (the safe default — nothing skipped by accident).

The workflow bumps `VERSION`/`pyproject.toml`, prepends a `CHANGELOG.md`
entry, commits straight to `main`, tags `vX.Y.Z`, and cuts a GitHub Release.

For pulling a new version into a project that already bootstrapped from an
earlier Vexa clone, use the prompt in
[docs/version-sync-prompt.md](docs/version-sync-prompt.md) — it targets a
specific release tag rather than a moving branch, and leaves a
`.vexa-version` marker behind so the next sync knows where it left off.

**Downstream projects get notified automatically.** `.claude/hooks/check_vexa_version.py`
runs as a `SessionStart` hook (registered in `.claude/settings.json`) in any
project bootstrapped from Vexa. It compares that project's `.vexa-version`
against Vexa's latest GitHub release and, if a newer one exists and the user
hasn't already dismissed it, has Claude ask **Yes (update now) / No (don't
ask again for this version) / Remind me tomorrow** via `AskUserQuestion`.
The choice is recorded in `.vexa-update-pref.json` (gitignored, per machine —
`skip_version` or `remind_after`). It self-excludes inside the Vexa framework
repo itself (checked via `origin`'s URL), fails silently offline, and never
blocks session start. This is orthogonal to `bootstrap.py`'s own copy of this
repo's files — a project only has this hook once it's synced at least once
via `docs/version-sync-prompt.md` (or was bootstrapped from a Vexa version
that already ships it).

## Skills

Repo-owned, under `.claude/skills/`:

- **`setup-vexa`** — configure a fresh clone to the user's app in one go
  (drives `bootstrap.py`). Never handles the user's password.
- **`verify-ticket`** — end-to-end workflow to reproduce/confirm a tracker ticket:
  verify live, capture evidence, back it with a pytest test, post the verdict
  using [docs/templates/qa-comment-template.md](docs/templates/qa-comment-template.md).
- **`write-ui-test`** — scaffold a new page object + UI test that follows these
  conventions.
- **`write-api-test`** — scaffold an authenticated API test using `ApiLibrary`.
- **`write-performance-test`** — scaffold a k6 script (smoke/load/stress/spike/soak)
  reusing `ApiLibrary`'s captured cookie and the repo's report convention.
- **`k6-performance`** — vendored general k6 reference (executors, custom
  metrics, data-driven tests, best practices) for generic k6 syntax help.

For recommended **external** plugins/MCP servers (Playwright MCP, superpowers,
pytest-patterns, accessibility-auditor), see
[docs/recommended-claude-setup.md](docs/recommended-claude-setup.md) — they're
installed via the plugin manager, not vendored here.
