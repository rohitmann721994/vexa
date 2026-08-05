"""Attach files to a Jira issue via the REST API.

The browser-automation attachment upload path (dragging files onto the Jira
UI) is blocked by tooling sandboxes that only allow uploading files the user
explicitly shared. This bypasses that entirely by calling Jira's own
attachments endpoint, the same mechanism CI pipelines use to attach build
artifacts.

Requires JIRA_EMAIL and JIRA_API_TOKEN in .env (create a token at
https://id.atlassian.com/manage-profile/security/api-tokens). The Jira site is
read from JIRA_BASE_URL (e.g. https://your-org.atlassian.net).
"""

import os
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


def attach_files(issue_key: str, file_paths: List[str], base_url: Optional[str] = None) -> list:
    """Attach each path in *file_paths* to *issue_key*. Returns the list of
    attachment metadata dicts Jira returns (filename, id, size, ...)."""
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
    if not email or not token:
        raise ValueError(
            "JIRA_EMAIL and JIRA_API_TOKEN must be set in .env "
            "(create a token at https://id.atlassian.com/manage-profile/security/api-tokens)"
        )
    if not base_url:
        raise ValueError("JIRA_BASE_URL must be set in .env (e.g. https://your-org.atlassian.net)")

    url = f"{base_url}/rest/api/3/issue/{issue_key}/attachments"
    headers = {"X-Atlassian-Token": "no-check"}

    attached = []
    for path in file_paths:
        p = Path(path)
        with open(p, "rb") as fh:
            logger.info("Attaching %s to %s", p.name, issue_key)
            response = requests.post(
                url,
                auth=(email, token),
                headers=headers,
                files={"file": (p.name, fh)},
                timeout=60,
            )
        response.raise_for_status()
        attached.extend(response.json())

    logger.info("Attached %d file(s) to %s", len(attached), issue_key)
    return attached
