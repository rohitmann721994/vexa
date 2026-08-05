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
- **AI-assistant ready** — a `CLAUDE.md` ruleset and two Claude Code skills
  (`verify-ticket`, `write-ui-test`) ship in the repo.

---

## Prerequisites

- **Python 3.14** — pinned via `requires-python = "==3.14.*"` in `pyproject.toml`
  (`uv` installs it for you).
- **[uv](https://github.com/astral-sh/uv)** — the dependency manager/runner.

---

## Quick start

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
.claude/skills/           # verify-ticket, write-ui-test
docs/                     # setup guide + pytest patterns reference
libraries/                # UiLibrary, ApiLibrary (facades)
pages/ui/                 # LoginPage, HomePage (page objects)
tests/                    # ui/ + api/ + fixtures
utils/                    # logger, evidence
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
