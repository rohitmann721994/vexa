import os
from typing import Optional

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

from pages.ui.login_page import LoginPage
from utils.logger import get_logger

# Load environment variables from .env in the project root (run via `uv run`
# from the root, so cwd is the root).
load_dotenv()


class UiLibrary:
    """High-level facade tests call for browser lifecycle + login.

    Tests never touch Playwright directly — they call ``open_application`` /
    ``login_with_credentials`` / ``close_application`` and then act through
    page objects on ``self.page``.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url or os.getenv("UI_BASE_URL", "")
        self._playwright = None
        self._browser = None
        self._page: Optional[Page] = None
        self._login_page: Optional[LoginPage] = None
        self._logger = get_logger(__name__)

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Application is not open. Call open_application() first.")
        return self._page

    def open_application(self, base_url: Optional[str] = None, headless: bool = True) -> None:
        """Start Playwright and open a new browser page."""
        if base_url:
            self._base_url = base_url
        if not self._base_url:
            raise RuntimeError("No UI base URL set. Pass base_url or set UI_BASE_URL in .env.")

        # Engine selectable for cross-browser runs: chromium | firefox | webkit.
        engine = (os.getenv("VEXA_BROWSER") or os.getenv("JURY_BROWSER") or "chromium").strip().lower()
        self._logger.info(
            "Opening application at %s (headless=%s, browser=%s)",
            self._base_url, headless, engine,
        )
        self._playwright = sync_playwright().start()
        launchers = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }
        launcher = launchers.get(engine, self._playwright.chromium)
        self._browser = launcher.launch(headless=headless)
        self._page = self._browser.new_page()
        self._login_page = LoginPage(self._page)
        self._login_page.open(self._base_url)

    def close_application(self) -> None:
        """Close the browser and stop Playwright. Safe to call more than once."""
        self._logger.info("Closing browser and stopping Playwright")
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._browser = None
        self._page = None
        self._login_page = None

    def login_with_credentials(self, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """Log in via the login page object. Falls back to QA_USERNAME /
        QA_PASSWORD from the environment when args are omitted."""
        if not self._login_page:
            raise RuntimeError("Application is not open. Call open_application() first.")
        user = username or os.getenv("QA_USERNAME")
        pwd = password or os.getenv("QA_PASSWORD")
        if not user or not pwd:
            raise RuntimeError(
                "Login credentials missing. Pass username/password or set "
                "QA_USERNAME and QA_PASSWORD in .env."
            )
        self._logger.info("Logging in as %s", user)
        self._login_page.login_as(user, pwd)

    def navigate(self, url: str) -> None:
        """Navigate the current page to an absolute or app-relative URL."""
        target = url if url.startswith("http") else self._base_url.rstrip("/") + "/" + url.lstrip("/")
        self._logger.info("Navigating to %s", target)
        self.page.goto(target, wait_until="domcontentloaded", timeout=120000)
