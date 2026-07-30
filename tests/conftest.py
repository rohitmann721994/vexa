import pytest

from libraries.ui_library import UiLibrary


@pytest.fixture
def uiLibrary():
    """Function-scoped UiLibrary; auto-closes the browser on teardown."""
    library_instance = UiLibrary()
    yield library_instance
    library_instance.close_application()
