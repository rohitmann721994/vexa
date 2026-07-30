"""API test fixtures.

``api_library`` is session-scoped so the browser login (and cookie capture)
happens only once per test run; ``api_session`` exposes the authenticated
``requests.Session`` derived from it.
"""

import pytest

from libraries.api_library import ApiLibrary


@pytest.fixture(scope="session")
def api_library():
    lib = ApiLibrary()
    # Build/reuse the authenticated session up front so the first test doesn't
    # pay the login cost mid-assertion.
    lib.session()
    return lib


@pytest.fixture(scope="session")
def api_session(api_library):
    return api_library.session()
