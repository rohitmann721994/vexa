# Vexa — QA Test Automation Framework

![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8%2B-0A9EDC?logo=pytest&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.6x-2EAD33?logo=playwright&logoColor=white)
![uv](https://img.shields.io/badge/deps-uv-DE5FE9?logo=uv&logoColor=white)
![UI + API](https://img.shields.io/badge/tests-UI%20%2B%20API-6E56CF)
![License](https://img.shields.io/badge/license-Proprietary-red)

A reusable Python test-automation framework for Catalis QA teams: `uv` +
`pytest` + Playwright, with a clean layered design (facades → page objects →
tests), evidence capture, HTML reporting, and ready-to-use AI-assistant rules
and skills.

Drop it in front of any web app behind an SPA / SSO login and you get UI **and**
API automation from one browser-login mechanism.

**Created and authored by Rohit Mann.** Maintained by Catalis QA.

---

## Features

- **Layered design** — tests never touch Playwright directly; they call library
  facades that delegate to page objects. Boundaries stay clean as the suite grows.
- **UI + API from one login** — API tests reuse a real browser login to capture
  session cookies, so SSO-protected JSON endpoints are testable with `requests`.
- **Evidence built in** — annotated screenshots + a per-test `steps.md` you can
  attach to a tracker ticket as proof.
- **Timestamped HTML reports** — self-contained, one per run, screenshot-on-failure.
- **Performance testing (k6)** — a `k6/` module (smoke/load/stress/spike/soak)
  reuses the same authenticated session as the API suite and writes the same
  self-contained HTML+JSON report style to `reports/`, plus an executive
  "results at a glance" tile-grid summary report for handing to a ticket or
  leadership; see `docs/performance-testing-guide.md`.
- **AI-assistant ready** — a `CLAUDE.md` ruleset and Claude Code skills
  (`verify-ticket`, `write-ui-test`, `write-api-test`, `write-performance-test`,
  plus vendored `k6-performance`) ship in the repo; see
  `docs/recommended-claude-setup.md` for recommended external plugins.
- **CI included** — a GitHub Actions workflow runs the suite on every push/PR.

---

## Prerequisites

- **Python 3.14** — pinned via `requires-python = "==3.14.*"` in `pyproject.toml`
  (`uv` installs it for you).
- **[uv](https://github.com/astral-sh/uv)** — the dependency manager/runner.

---

## Set up for your project (one command)

Clone, then run the bootstrap — it configures the framework to *your* app
(project name, URL, login selectors, `.env`, dependencies, a starter test) in
one go:

```bash
git clone https://github.com/rohitmann721994/vexa my-project
cd my-project
uv run python bootstrap.py
```

The only manual step it leaves you is pasting your test password into `.env`.
Prefer to do it from Claude? Ask it to **"set up vexa for my project"** — the
`setup-vexa` skill runs the same flow interactively (it configures everything
except the password, which you add yourself).

Want to see what it'll do first? Add `--dry-run` — it prints every change
(the `.env` it would write, the rename, the files it would swap, the commands
it would run) and touches nothing:

```bash
uv run python bootstrap.py --dry-run
```

## Manual quick start

```bash
# one-time
uv sync
uv run playwright install
cp .env.example .env        # then edit for your app

# every run
uv run pytest -m ui         # report → reports/report_<timestamp>.html
```

On a fresh clone the example test **skips** until you set `UI_BASE_URL` in `.env`,
so `uv run pytest` is green immediately.

---

## Adapting it to your app

See **[docs/framework-setup-guide.md](docs/framework-setup-guide.md)** for the
full walkthrough. In short:

1. Set `UI_BASE_URL`, `QA_USERNAME`, `QA_PASSWORD` in `.env`.
2. Adjust the login selectors in `.env` (or add an SSO page object) —
   see `pages/ui/login_page.py`.
3. Copy `tests/ui/test_example_login.py` and `pages/ui/home_page.py` as templates
   for your first real page object + test.

---

## Layout

```
CLAUDE.md                 # AI-assistant rules (architecture, conventions, gotchas)
pyproject.toml pytest.ini conftest.py   # toolchain + scaffolding
.env.example .gitignore
.claude/skills/           # verify-ticket, write-ui-test, write-api-test,
                          # write-performance-test, k6-performance
docs/                     # setup guide + pytest patterns + performance testing guide
                          # + templates/qa-comment-template.md
libraries/                # UiLibrary, ApiLibrary (facades)
pages/ui/                 # LoginPage, HomePage (page objects)
tests/                    # ui/ + api/ + fixtures
utils/                    # logger, evidence
k6/                       # performance testing module (smoke/load/stress/spike/soak)
```

See `CLAUDE.md` for the architecture and the (important) authentication notes.

---

## Author & Credits

**Vexa was created and authored by Rohit Mann** — framework design, architecture,
and the AI-assistant rules and skills. Maintained by Catalis QA.

## License

Copyright (c) 2026 Rohit Mann. All rights reserved. See [LICENSE](LICENSE).
Ownership and final terms are subject to any applicable employment agreements —
the current notice is a placeholder pending that confirmation.
