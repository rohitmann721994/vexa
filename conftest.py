"""Root pytest configuration.

- Names each run's HTML report with a timestamp under ``reports/``.
- Attaches a screenshot to the HTML report on failure when a Playwright
  ``page`` (or legacy ``driver``) funcarg is present.
"""

import os
from datetime import datetime

import pytest


def pytest_configure(config):
    # 1. Ensure the reports folder exists.
    os.makedirs("reports", exist_ok=True)

    # 2. Timestamp for this run (e.g. 2026-07-30_22-25-23).
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 3. Point pytest-html at a per-run, self-contained report.
    #    Guard: htmlpath only exists when the pytest-html plugin is loaded.
    if hasattr(config, "option") and hasattr(config.option, "htmlpath"):
        config.option.htmlpath = f"reports/report_{timestamp}.html"
        config.option.self_contained_html = True


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a screenshot to the HTML report on UI test failure."""
    outcome = yield
    report = outcome.get_result()

    extra = getattr(report, "extra", [])

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        driver = item.funcargs.get("driver")
        try:
            from pytest_html import extras as html_extras

            screenshot_name = f"{item.name}_failed.png"
            screenshot_path = os.path.join("reports", screenshot_name)
            if page is not None:  # Playwright
                page.screenshot(path=screenshot_path, full_page=True)
                extra.append(html_extras.image(screenshot_name))
            elif driver is not None:  # legacy Selenium WebDriver
                driver.save_screenshot(screenshot_path)
                extra.append(html_extras.image(screenshot_name))
        except Exception:
            pass  # Never let screenshot capture break the report.

    report.extra = extra
