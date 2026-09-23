"""SessionStart hook: checks whether a newer Vexa release exists and, unless
the user already chose "No" or "remind me later" for it, tells Claude to ask.

Prints nothing (never blocks/slows session start) when: offline, rate
limited, already up to date, the user dismissed this exact version, still
inside a "remind me tomorrow" window, or this IS the Vexa framework repo
itself (checked via origin URL) rather than a project built from it.

State lives in two small files at the project root:
  .vexa-version           committed — the version this project last synced to
  .vexa-update-pref.json  gitignored, per-machine — {"skip_version": "vX.Y.Z"}
                          and/or {"remind_after": "YYYY-MM-DD"}
"""

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

REPO = "rohitmann721994/vexa"
ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / ".vexa-version"
PREF_FILE = ROOT / ".vexa-update-pref.json"
TIMEOUT = 3


def _origin_url() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _current_version() -> str:
    if VERSION_FILE.exists():
        v = VERSION_FILE.read_text(encoding="utf-8").strip()
        if v:
            return v
    return "v0.1.0"


def _latest_release():
    try:
        req = Request(
            f"https://api.github.com/repos/{REPO}/releases/latest",
            headers={"User-Agent": "vexa-version-check"},
        )
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
        return data.get("tag_name"), data.get("body", "") or "", data.get("html_url", "")
    except Exception:
        return None, "", ""


def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0,)


def _load_pref() -> dict:
    if PREF_FILE.exists():
        try:
            return json.loads(PREF_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def main() -> None:
    if REPO in _origin_url():
        return  # this IS the Vexa framework repo — nothing to update to

    current = _current_version()
    latest, notes, url = _latest_release()
    if not latest:
        return  # offline, rate-limited, or API error — stay silent

    if _version_tuple(latest) <= _version_tuple(current):
        return  # already up to date

    pref = _load_pref()
    skip_version = pref.get("skip_version")
    if skip_version and _version_tuple(latest) <= _version_tuple(skip_version):
        return  # user said No for this version already

    remind_after = pref.get("remind_after")
    if remind_after and date.today().isoformat() < remind_after:
        return  # still inside the "remind me tomorrow" window

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    print(f"""VEXA_UPDATE_AVAILABLE
Current project version: {current}
Latest Vexa release: {latest} ({url})

Changelog:
{notes.strip() or '(see ' + url + ')'}

Near the start of this session - once, not repeatedly, and not ahead of
anything the user is already asking for - ask via AskUserQuestion: header
"Vexa update", one question, three options:
  - "Yes - update now": follow docs/version-sync-prompt.md to sync this
    project from {current} to {latest} (add the vexa-upstream remote, diff
    new vs. already-customized files, merge, update .vexa-version to
    {latest}), then delete .vexa-update-pref.json if it exists.
  - "No - don't ask again for this version": write {{"skip_version": "{latest}"}}
    to .vexa-update-pref.json at the project root (create or overwrite it,
    preserving any other keys already in it). Don't ask again unless a
    version newer than {latest} is released.
  - "Remind me tomorrow": write {{"remind_after": "{tomorrow}"}} to
    .vexa-update-pref.json at the project root (preserving any other keys).
""")


if __name__ == "__main__":
    main()
