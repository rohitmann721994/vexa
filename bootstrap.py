#!/usr/bin/env python3
"""Vexa one-command setup.

Turns a fresh clone of the Vexa framework into a ready-to-code test-automation
repo configured for YOUR app. Run it once, right after cloning:

    git clone https://github.com/rohitmann721994/vexa my-project
    cd my-project
    uv run python bootstrap.py

It will (in order):
  1. Collect your project + app details (interactive prompts, or --config JSON).
  2. Write a project-specific .env (gitignored — never committed).
  3. Rename the project (pyproject.toml + a fresh README), keeping a credit to
     the Vexa framework (created by Rohit Mann).
  4. Replace the shipped examples with a starter smoke test named for your app.
  5. Install the toolchain (uv sync + Playwright chromium).
  6. Optionally reset git history to a clean initial commit for your repo.
  7. Verify the repo collects, and print next steps.

Stdlib only — no third-party imports — so it runs before dependencies exist.

MODES
  Interactive (default):  uv run python bootstrap.py
  Non-interactive:        uv run python bootstrap.py --config bootstrap.json [--yes]
    (used by the setup-vexa Claude skill and by CI; a password is never required
     and is left blank for the user to fill in.)

FLAGS
  --config PATH   Read answers from a JSON file instead of prompting.
  --yes           Assume "yes" for confirmations (e.g. the git reset).
  --no-password   Never prompt for / write a password (leave QA_PASSWORD blank).
  --no-install    Skip `uv sync` and `playwright install`.
  --no-git-reset  Keep existing git history (skip the clean re-init).
  --dry-run       Print what every step WOULD do; write nothing, run nothing,
                  leave git untouched. Safe to run in any repo to preview.
"""

import argparse
import getpass
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VEXA_UPSTREAM_MARKER = "rohitmann721994/vexa"


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s or "my-project"


def pkg_name(text: str) -> str:
    """A valid PEP 508 project name (hyphens ok)."""
    return slugify(text)


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{label}{suffix}: ").strip()
    except EOFError:
        val = ""
    return val or default


def prompt_bool(label: str, default: bool = True) -> str:
    d = "Y/n" if default else "y/N"
    try:
        val = input(f"{label} [{d}]: ").strip().lower()
    except EOFError:
        val = ""
    if not val:
        return default
    return val in ("y", "yes")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check)


def run(cmd: list, check: bool = True) -> int:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT, check=check).returncode


def _force_rmtree(path: Path) -> None:
    def onerror(func, p, exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=onerror)


def _would(msg: str) -> None:
    print(f"    [dry-run] would {msg}")


# --------------------------------------------------------------------------- #
# config collection
# --------------------------------------------------------------------------- #
def default_author() -> str:
    try:
        return git("config", "user.name", check=False).stdout.strip()
    except Exception:
        return ""


def collect_config(args) -> dict:
    if args.config:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        cfg.setdefault("password", "")
        return cfg

    print("\n=== Vexa setup — tell me about your project ===\n")
    name = prompt("Project name", ROOT.name)
    cfg = {
        "project_name": name,
        "author": prompt("Your name (project author)", default_author()),
        "description": prompt("One-line description", f"{name} test automation"),
        "ui_base_url": prompt("App URL (UI_BASE_URL)", "https://your-app.example.com"),
        "username": prompt("Test username (QA_USERNAME)", ""),
        "login_username_selector": prompt("Login username selector", "#UserName"),
        "login_password_selector": prompt("Login password selector", "#Password"),
        "login_submit_selector": prompt("Login submit selector", "input[type=submit]"),
        "login_success_selector": prompt("Post-login success selector (optional)", ""),
    }
    cfg["include_api"] = prompt_bool("Include API testing?", True)
    cfg["api_base_url"] = (
        prompt("API base URL (API_BASE_URL)", cfg["ui_base_url"].rstrip("/") + "/api")
        if cfg["include_api"] else ""
    )
    cfg["jira_base_url"] = prompt("Jira base URL (optional, for verify-ticket)", "")
    cfg["jira_email"] = prompt("Jira email (optional)", "")

    if args.no_password or args.dry_run:
        cfg["password"] = ""
    else:
        pw = getpass.getpass("Test password (QA_PASSWORD, hidden — Enter to skip): ")
        cfg["password"] = pw
    return cfg


# --------------------------------------------------------------------------- #
# steps
# --------------------------------------------------------------------------- #
def write_env(cfg: dict, dry: bool = False) -> None:
    print("\n[1/6] Writing .env")
    lines = [
        f"# {cfg['project_name']} - environment configuration (generated by bootstrap.py).",
        "# This file is gitignored. Never commit real credentials.",
        "",
        f"UI_BASE_URL={cfg.get('ui_base_url', '')}",
        f"QA_USERNAME={cfg.get('username', '')}",
        f"QA_PASSWORD={cfg.get('password', '')}",
        "VEXA_BROWSER=chromium",
        "",
        "# Login form selectors",
        f"LOGIN_USERNAME_SELECTOR={cfg.get('login_username_selector', '#UserName')}",
        f"LOGIN_PASSWORD_SELECTOR={cfg.get('login_password_selector', '#Password')}",
        f"LOGIN_SUBMIT_SELECTOR={cfg.get('login_submit_selector', 'input[type=submit]')}",
        f"LOGIN_SUCCESS_SELECTOR={cfg.get('login_success_selector', '')}",
        "",
        "# API",
        f"API_BASE_URL={cfg.get('api_base_url', '')}",
        "API_COOKIES=",
        "",
        "# Jira attachment upload (optional)",
        f"JIRA_EMAIL={cfg.get('jira_email', '')}",
        "JIRA_API_TOKEN=",
        f"JIRA_BASE_URL={cfg.get('jira_base_url', '')}",
        "",
    ]
    if dry:
        _would("write .env:")
        for ln in lines:
            if ln.startswith("QA_PASSWORD=") and cfg.get("password"):
                ln = "QA_PASSWORD=***"
            print(f"      | {ln}")
        return
    (ROOT / ".env").write_text("\n".join(lines), encoding="utf-8")
    if not cfg.get("password"):
        print("    NOTE: QA_PASSWORD left blank - add it to .env before running UI tests.")


def rename_project(cfg: dict, dry: bool = False) -> None:
    print("[2/6] Renaming project")
    name = pkg_name(cfg["project_name"])
    desc = cfg.get("description", "").replace('"', "'")

    if dry:
        author = cfg.get("author", "")
        _would(f'set pyproject.toml name="{name}", description="{desc}"'
                + (f', author="{author}"' if author else ""))
        _would("regenerate README.md for the project (keeps a Vexa credit line)")
        return

    pp = ROOT / "pyproject.toml"
    text = pp.read_text(encoding="utf-8")
    text = re.sub(r'^name = ".*"', f'name = "{name}"', text, count=1, flags=re.MULTILINE)
    text = re.sub(r'^description = ".*"', f'description = "{desc}"', text, count=1, flags=re.MULTILINE)
    if cfg.get("author"):
        author = cfg["author"].replace('"', "'")
        text = re.sub(
            r"authors = \[\s*\{ name = \".*\" \},?\s*\]",
            f'authors = [\n    {{ name = "{author}" }},\n]',
            text, count=1,
        )
    pp.write_text(text, encoding="utf-8")

    readme = f"""# {cfg['project_name']}

{cfg.get('description', '')}

Test automation for **{cfg['project_name']}**, built with `uv` + `pytest` +
Playwright (UI{' + API' if cfg.get('include_api') else ''}).

## Quick start

```bash
uv sync
uv run playwright install
uv run pytest
```

Configuration lives in `.env` (gitignored). See `docs/framework-setup-guide.md`
for the full guide and `CLAUDE.md` for architecture + conventions.

---

Built on the [Vexa](https://github.com/rohitmann721994/vexa) test-automation
framework, created by Rohit Mann.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def swap_examples(cfg: dict, dry: bool = False) -> None:
    print("[3/6] Replacing examples with a starter test")
    slug = slugify(cfg["project_name"]).replace("-", "_")

    if dry:
        for rel in ("tests/ui/test_example_login.py", "tests/api/test_example_api.py"):
            if (ROOT / rel).exists():
                _would(f"delete {rel}")
        _would(f"create tests/ui/test_{slug}_smoke.py (starter smoke test)")
        return

    for rel in ("tests/ui/test_example_login.py", "tests/api/test_example_api.py"):
        p = ROOT / rel
        if p.exists():
            p.unlink()

    smoke = f'''"""Starter smoke test for {cfg['project_name']}.

Logs in and confirms a post-login page renders. Skips cleanly until UI_BASE_URL
is set in .env. Copy this shape for real tests: a marker, the uiLibrary +
evidence fixtures, page objects for locators, assertions that print observed state.
"""

import os

import pytest

from pages.ui.home_page import HomePage

pytestmark = pytest.mark.skipif(
    not os.getenv("UI_BASE_URL"),
    reason="UI_BASE_URL not set — configure .env to run this test.",
)


@pytest.mark.ui
@pytest.mark.smoke
def test_login_reaches_app(uiLibrary, evidence):
    evidence.scenario(
        "Login smoke test",
        "Logging in with valid credentials reaches the post-login app.",
    )
    uiLibrary.open_application(headless=True)
    uiLibrary.login_with_credentials()
    home = HomePage(uiLibrary.page)
    loaded = home.is_loaded(os.getenv("LOGIN_SUCCESS_SELECTOR", ""))
    evidence.step(uiLibrary.page, "After login")
    assert loaded, f"No post-login page rendered. URL: {{uiLibrary.page.url}}"
'''
    (ROOT / "tests" / "ui" / f"test_{slug}_smoke.py").write_text(smoke, encoding="utf-8")

    if not cfg.get("include_api"):
        # Keep the api fixtures (harmless), just ensure no example lingers.
        pass


def install_toolchain(args) -> None:
    print("[4/6] Installing toolchain")
    if args.dry_run:
        _would("run: uv sync")
        _would("run: uv run playwright install chromium")
        return
    if args.no_install:
        print("    skipped (--no-install)")
        return
    if shutil.which("uv") is None:
        print("    WARNING: 'uv' not found on PATH — skipping. Install uv, then run:")
        print("             uv sync && uv run playwright install chromium")
        return
    run(["uv", "sync"], check=False)
    run(["uv", "run", "playwright", "install", "chromium"], check=False)


def reset_git(args) -> None:
    print("[5/6] Git")
    if args.no_git_reset:
        print("    keeping existing history (--no-git-reset)")
        return

    origin = git("remote", "get-url", "origin", check=False).stdout.strip()
    if VEXA_UPSTREAM_MARKER in origin:
        if args.dry_run:
            print(f"    [dry-run] would REFUSE: origin is the Vexa framework repo ({origin}).")
        else:
            print(f"    REFUSING: origin is the Vexa framework repo ({origin}).")
            print("    Re-clone into your own project dir, or pass --no-git-reset. Skipping.")
        return

    if args.dry_run:
        _would("reset .git and create a fresh 'Initial commit (bootstrapped from Vexa)'")
        return

    if not args.yes:
        if not prompt_bool("    Reset git history to a clean initial commit?", True):
            print("    keeping existing history")
            return

    if (ROOT / ".git").exists():
        _force_rmtree(ROOT / ".git")
    git("init", check=False)
    git("add", "-A", check=False)
    git("commit", "-m", "Initial commit (bootstrapped from Vexa)", check=False)
    print("    fresh git history created")


def verify(args) -> None:
    print("[6/6] Verifying the repo collects")
    if args.dry_run:
        print("    [dry-run] would run: uv run pytest --co -q")
        return
    if shutil.which("uv") is None:
        print("    skipped (uv not found)")
        return
    subprocess.run(["uv", "run", "pytest", "--co", "-q"], cwd=ROOT, check=False)


def print_next_steps(cfg: dict) -> None:
    print("\n=== Done. Vexa is set up for", cfg["project_name"], "===\n")
    print("Next steps:")
    if not cfg.get("password"):
        print("  1. Add your test password:  QA_PASSWORD=... in .env")
    print("  2. Confirm the login selectors in .env match your app's login form.")
    print("  3. Run the suite:            uv run pytest -m ui")
    print("  4. Write your first test - ask Claude to use the write-ui-test skill,")
    print("     or copy the generated starter test in tests/ui/.")
    print()


# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Vexa one-command setup.")
    parser.add_argument("--config", help="JSON file of answers (non-interactive).")
    parser.add_argument("--yes", action="store_true", help="Assume yes for confirmations.")
    parser.add_argument("--no-password", action="store_true", help="Never handle a password.")
    parser.add_argument("--no-install", action="store_true", help="Skip uv sync / playwright.")
    parser.add_argument("--no-git-reset", action="store_true", help="Keep git history.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview every step; write nothing, run nothing, git untouched.")
    args = parser.parse_args()

    if args.dry_run:
        print("\n*** DRY RUN - previewing changes; nothing is written, installed, or committed ***")

    cfg = collect_config(args)
    write_env(cfg, args.dry_run)
    rename_project(cfg, args.dry_run)
    swap_examples(cfg, args.dry_run)
    install_toolchain(args)
    reset_git(args)
    verify(args)
    print_next_steps(cfg)
    if args.dry_run:
        print("Dry run complete - no changes made. Re-run without --dry-run to apply.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
