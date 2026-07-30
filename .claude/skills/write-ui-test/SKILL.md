---
name: write-ui-test
description: Use when adding a new UI test to this Vexa repo — scaffolding a page object plus a pytest test that follow the framework's layered conventions. Triggers include "write a UI test for X", "add a test for this page/feature", "create a page object for X", "automate this UI flow".
---

# Write a UI Test

## Overview

Scaffold a new UI test the way this framework expects: locators + actions in a
page object under `pages/ui/`, assertions in a test under `tests/ui/`, using the
`uiLibrary` and `evidence` fixtures. Read `CLAUDE.md` first for the architecture
and conventions.

**The golden rule: page objects hold locators and actions; tests hold
assertions. No raw Playwright calls in tests, no assertions in page objects.**

## Steps

Track these as todos; do them in order.

### 1. Confirm the flow and selectors live

Before writing code, drive the flow interactively (Playwright MCP, headed) to
capture real, stable selectors. Prefer role/text/id selectors over brittle CSS
paths. Note anything that only works headed, or any dialog/flag/precondition.

### 2. Create or extend the page object

`pages/ui/<page>.py` — one class per screen. Locators in `__init__`, one method
per meaningful action or query. No assertions. Follow `pages/ui/home_page.py`:

```python
from playwright.sync_api import Page


class WidgetPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.save_button = "#save"
        self.status_label = "#status"

    def save(self) -> None:
        self.page.click(self.save_button)

    def status_text(self) -> str:
        return (self.page.text_content(self.status_label) or "").strip()
```

### 3. Write the test

`tests/ui/test_<feature>.py`. Follow `tests/ui/test_example_login.py`:

```python
import pytest

from pages.ui.widget_page import WidgetPage


@pytest.mark.ui
def test_saving_widget_persists(uiLibrary, evidence):
    evidence.scenario(
        "Widget save persists",
        "Saving a widget stores it server-side and shows a success status.",
        criteria=["Save shows success", "Value survives a reload"],
    )

    uiLibrary.open_application(headless=True)
    uiLibrary.login_with_credentials()
    uiLibrary.navigate("widgets")

    widget = WidgetPage(uiLibrary.page)
    widget.save()
    evidence.annotated_step(uiLibrary.page, "Clicked Save", expected="Status shows 'Saved'.")

    # Assert authoritative server state — reload, don't trust the optimistic UI.
    uiLibrary.page.reload()
    assert widget.status_text() == "Saved", f"Observed status: {widget.status_text()!r}"
```

Requirements:
- Exactly one registered marker minimum (`@pytest.mark.ui`); add `smoke` /
  `regression` / `ticket("ABC-123")` as they apply (register new markers in
  `pytest.ini` first — `--strict-markers` is on).
- Use `uiLibrary` (browser lifecycle + login) and `evidence` (proof).
- Assertion messages print the observed state so a failure is self-explanatory.
- Verify final state against the server (reload), not the optimistic in-page result.

### 4. Run it and confirm a real PASS

```bash
uv run pytest tests/ui/test_<feature>.py -m ui
```

Report the actual outcome. If it only passes headed, say so — don't claim a
headless PASS you didn't get. Never leave a test asserting a bug is fixed when
it isn't (use `xfail(strict=True)` instead).

## Common Mistakes

- Raw `page.click(...)` / locators inline in the test instead of a page object.
- Assertions inside the page object.
- Asserting the optimistic in-page result instead of reloading server state.
- Unregistered marker (fails under `--strict-markers`).
- `print()` instead of the logger; plain `step()` where `annotated_step` is wanted.
