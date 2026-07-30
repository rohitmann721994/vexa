from playwright.sync_api import Page


class HomePage:
    """Example page object for the post-login landing page.

    Page objects hold locators + page-level actions ONLY — no assertions, no
    test logic. Tests call these methods; assertions live in the test. Replace
    the locators below with your app's real selectors.
    """

    def __init__(self, page: Page) -> None:
        self.page = page
        # Example locators — replace with your app's.
        self.header = "h1"
        self.user_menu = "#user-menu"

    def get_header_text(self) -> str:
        return (self.page.text_content(self.header) or "").strip()

    def is_loaded(self, success_selector: str = "") -> bool:
        """True once the post-login page is ready. If a success selector is
        given, wait for it; otherwise fall back to the header being present."""
        selector = success_selector or self.header
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=30000)
            return True
        except Exception:
            return False
