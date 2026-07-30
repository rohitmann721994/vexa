import os

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class LoginPage:
    """Page object for a classic single-form login.

    Username + password on one page, submitted with a single button. Selectors
    default to a common ASP.NET-style form but are overridable via environment
    variables so this page object works against most apps without edits:

      LOGIN_USERNAME_SELECTOR   (default '#UserName')
      LOGIN_PASSWORD_SELECTOR   (default '#Password')
      LOGIN_SUBMIT_SELECTOR     (default 'input[type=submit]')

    Apps with a multi-step / SSO / tenant-picker login should add a sibling
    page object (e.g. ``sso_login_page.py``) and select it in ``UiLibrary`` the
    way the source framework switched login flows by target.
    """

    def __init__(self, page: Page) -> None:
        self.page = page
        self.username_input = os.getenv("LOGIN_USERNAME_SELECTOR", "#UserName")
        self.password_input = os.getenv("LOGIN_PASSWORD_SELECTOR", "#Password")
        self.login_button = os.getenv("LOGIN_SUBMIT_SELECTOR", "input[type=submit]")

    def open(self, base_url: str) -> None:
        # Wait for the response to commit, then for DOM readiness separately —
        # more robust against slow SPAs than a single networkidle wait.
        self.page.goto(base_url, wait_until="commit", timeout=120000)
        self.page.wait_for_load_state("domcontentloaded", timeout=120000)

    def login_as(self, username: str, password: str) -> None:
        # The login form can be slow to render; reload once before giving up.
        try:
            self.page.wait_for_selector(self.username_input, state="visible", timeout=60000)
        except PlaywrightTimeoutError:
            self.page.reload(wait_until="domcontentloaded", timeout=120000)
            self.page.wait_for_selector(self.username_input, state="visible", timeout=60000)
        self.page.fill(self.username_input, username)
        self.page.fill(self.password_input, password)
        self.page.click(self.login_button, timeout=120000)
