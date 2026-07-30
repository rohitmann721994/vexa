# Setting Up Vexa for Your Project

A step-by-step guide for teammates who want to use this framework (`uv` +
`pytest` + Playwright, layered page-object design) as the starting point for
automating their own app.

Vexa ships app-agnostic: the login is a generic single-form flow with
overridable selectors, and the one example test skips until you point it at an
app. You configure `.env`, adjust selectors (or add an SSO page object), and
start writing page objects + tests.

> Vexa was created and authored by **Rohit Mann**.

---

## Part A — What you're working with

The value is in the layer separation. Learn it before adding code:

```
tests/            # pytest test functions ONLY (no locators, no Playwright calls)
libraries/        # facades tests call (UiLibrary, ApiLibrary)
pages/ui/         # Page Object Model — locators + page actions
utils/            # logger, evidence recorder
conftest.py       # root: report naming + screenshot-on-failure
tests/conftest.py         # uiLibrary fixture (browser per test)
tests/api/conftest.py     # api_library / api_session fixtures
tests/ui/conftest.py      # evidence fixture
pytest.ini        # markers, logging, pythonpath
pyproject.toml    # dependencies (managed by uv)
.env / .env.example       # credentials + URLs (never hard-code these)
```

---

## Part B — Prerequisites (one-time, per machine)

1. **Python 3.14** — `pyproject.toml` pins `requires-python = "==3.14.*"`. `uv`
   installs it for you, so you don't manage it by hand.
2. **[uv](https://github.com/astral-sh/uv)** — dependency manager/runner.
   Install on Windows PowerShell:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. **git**.

Verify:

```bash
uv --version
```

---

## Part C — Install the toolchain

From the project root:

```bash
uv sync
uv run playwright install
```

`uv sync` creates `.venv` and installs the pinned Python plus every dependency
(including the `dev` group). `playwright install` fetches the browser binaries.

> You never activate the venv. Prefix commands with `uv run`.

---

## Part D — Configure `.env`

```bash
cp .env.example .env
```

Fill in your app's values. Minimum to make the example test run:

```ini
UI_BASE_URL=https://your-app.example.com
QA_USERNAME=your_test_user
QA_PASSWORD=your_test_password
```

If your login form's fields aren't the defaults (`#UserName` / `#Password` /
`input[type=submit]`), override them:

```ini
LOGIN_USERNAME_SELECTOR=#email
LOGIN_PASSWORD_SELECTOR=#password
LOGIN_SUBMIT_SELECTOR=button[type=submit]
LOGIN_SUCCESS_SELECTOR=#dashboard   # a selector only present after login
```

`.env` is gitignored — never commit real credentials.

---

## Part E — Adapt the login (the one app-specific part)

Vexa handles a **classic single-form login** out of the box via
`pages/ui/login_page.py`, with selectors read from `.env`. For most apps you
just set the four selectors above and you're done.

If your app uses a **multi-step / SSO / tenant-picker** flow (Azure AD,
IdentityServer, Okta, ...), add a sibling page object — e.g.
`pages/ui/sso_login_page.py` — that encodes those steps, and select it in
`UiLibrary.open_application` based on an env var or a `--target` CLI option.
`UiLibrary` is small on purpose so this seam is easy to add.

---

## Part F — Write your first page object + test

**Page object** (`pages/ui/orders_page.py`) — locators + actions, no asserts:

```python
from playwright.sync_api import Page


class OrdersPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.new_order_button = "#new-order"
        self.order_row = ".order-row"

    def create_order(self) -> None:
        self.page.click(self.new_order_button)

    def order_count(self) -> int:
        return self.page.locator(self.order_row).count()
```

**Test** (`tests/ui/test_orders.py`) — uses `uiLibrary` + `evidence`:

```python
import pytest

from pages.ui.orders_page import OrdersPage


@pytest.mark.ui
def test_create_order_adds_a_row(uiLibrary, evidence):
    evidence.scenario("Create order", "Creating an order adds a row to the list.")
    uiLibrary.open_application(headless=True)
    uiLibrary.login_with_credentials()
    uiLibrary.navigate("orders")

    orders = OrdersPage(uiLibrary.page)
    before = orders.order_count()
    orders.create_order()
    evidence.annotated_step(uiLibrary.page, "Clicked New Order", expected="A new row appears.")

    uiLibrary.page.reload()
    assert orders.order_count() == before + 1, f"count went {before} -> {orders.order_count()}"
```

The `uiLibrary` fixture auto-closes the browser on teardown — no cleanup in the
test. The `write-ui-test` skill scaffolds this for you.

---

## Part G — API tests

`ApiLibrary` logs in through the browser once, captures the session cookies, and
gives you an authenticated `requests.Session`:

```python
import pytest


@pytest.mark.api
def test_orders_endpoint_ok(api_library):
    resp = api_library.get("orders")
    assert resp.status_code == 200, resp.text
```

Set `API_BASE_URL` in `.env`. Cookies are captured by intercepting the raw
`Cookie` header off the app's first authenticated request (keyed on
`API_COOKIE_TRIGGER`, default `/api/`) and cached to `.env` as `API_COOKIES=`.
If your backend uses chunked BFF cookies, read the Authentication section of
`CLAUDE.md` before touching the cookie logic.

---

## Part H — Run, report, evidence

```bash
uv run pytest                # full suite → reports/report_<timestamp>.html
uv run pytest -m ui          # UI only
uv run pytest -m api         # API only
uv run pytest -m smoke       # smoke only
uv run pytest -n auto        # parallel
```

- **HTML report:** self-contained `reports/report_<timestamp>.html` per run.
- **Logs:** console at INFO; full DEBUG at `logs/automation.log`. Use
  `from utils.logger import get_logger`.
- **Evidence:** the `evidence` fixture records annotated screenshots + `steps.md`
  under `reports/evidence/<test>/` (nested by ticket id when the test is marked
  `@pytest.mark.ticket("ABC-123")`).

Watch the browser: pass `headless=False` to `open_application(...)`. Switch
engines with `VEXA_BROWSER=firefox` (or `webkit`).

---

## Part I — Markers and discovery

Registered in `pytest.ini` (`--strict-markers` is on — add yours there first):
`ui`, `api`, `smoke`, `regression`, `slow`, `ticket`. Files must be named
`test_*.py` and functions `test_*` or they won't be collected. See
`docs/pytest-patterns.md` for fixtures/parametrize/marker patterns.

---

## Quick-start cheat sheet

```bash
uv sync
uv run playwright install
cp .env.example .env        # then edit UI_BASE_URL + creds
uv run pytest -m ui
```
