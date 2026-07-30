"""Shared fixtures for UI tests.

The ``evidence`` fixture records annotated screenshots + a ``steps.md`` per test.
When a test is marked ``@pytest.mark.ticket("ABC-123")`` the evidence directory
is nested under that ticket id (``reports/evidence/ABC-123/<test>/``); otherwise
it falls back to ``reports/evidence/<test>/``.
"""

import pytest

from utils.evidence import Evidence


@pytest.fixture
def evidence(request):
    """Per-test screenshot/evidence recorder; writes steps.md on teardown."""
    marker = request.node.get_closest_marker("ticket")
    if marker and marker.args:
        name = f"{marker.args[0]}/{request.node.name}"
    else:
        name = request.node.name
    ev = Evidence(name)
    yield ev
    ev.write()
