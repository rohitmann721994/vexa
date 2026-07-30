"""Example UI test — a template to copy, and a live smoke check.

It logs into the app under test and confirms the login lands somewhere valid.
On a fresh clone with no ``UI_BASE_URL`` configured it SKIPS cleanly, so
``uv run pytest`` is green out of the box. Fill in ``.env`` (UI_BASE_URL +
QA_USERNAME/QA_PASSWORD, and login selectors if your form differs) to make it run.

Copy this file's shape for real tests: a marker, the ``uiLibrary`` + ``evidence``
fixtures, page objects for locators, and assertions that carry the observed state.
"""

import os

import pytest

from pages.ui.home_page import HomePage

pytestmark = pytest.mark.skipif(
    not os.getenv("UI_BASE_URL"),
    reason="UI_BASE_URL not set — configure .env to run the example UI test.",
)


@pytest.mark.ui
@pytest.mark.smoke
def test_login_reaches_app(uiLibrary, evidence):
    evidence.scenario(
        "Login smoke test",
        "Logging in with valid credentials reaches the post-login app.",
        criteria=["Login form accepts credentials", "A post-login page renders"],
    )

    uiLibrary.open_application(headless=True)
    evidence.step(uiLibrary.page, "Login page loaded")

    uiLibrary.login_with_credentials()  # reads QA_USERNAME / QA_PASSWORD from .env

    home = HomePage(uiLibrary.page)
    success_selector = os.getenv("LOGIN_SUCCESS_SELECTOR", "")
    loaded = home.is_loaded(success_selector)
    evidence.step(uiLibrary.page, "After login")

    assert loaded, (
        "Expected a post-login page to render "
        f"(waited for selector: {success_selector or home.header!r}). "
        f"Current URL: {uiLibrary.page.url}"
    )
