---
name: setup-vexa
description: Use when setting up this Vexa framework for a new project — configuring a fresh clone to the user's own app in one go (project name, app URL, login selectors, .env, dependencies, starter test). Triggers include "set up vexa for my project", "bootstrap this framework", "configure vexa for my app", "one-command setup".
---

# Set Up Vexa for a Project

## Overview

Drive `bootstrap.py` to turn a fresh Vexa clone into a ready-to-code repo
configured for the user's app — so the only manual step they're left with is
pasting their password into `.env`. Everything else is automated.

Read `bootstrap.py`'s docstring for exactly what it does. Your job is to gather
the inputs, run it non-interactively, and confirm the result.

## Password safety (non-negotiable)

**You must never collect, type, or write the user's password.** Handling
passwords in plaintext is prohibited. So:

- Gather everything EXCEPT the password.
- Run `bootstrap.py` with `--no-password` so it never prompts for or writes one.
- After it finishes, tell the user to add the single line `QA_PASSWORD=...` to
  `.env` themselves.

If the user pastes a password to you anyway, do not put it into any file or
command — remind them to add it to `.env` directly.

## Workflow

Track these as todos; do them in order.

### 1. Confirm the starting point

- Confirm the user is in a **fresh clone** meant to become their project (not the
  Vexa framework repo itself). `bootstrap.py` refuses the git reset if `origin`
  is the Vexa upstream, but check anyway.
- Confirm they have `uv` installed (`uv --version`). If not, point them at
  https://github.com/astral-sh/uv and stop.

### 2. Gather inputs (ask the user)

Use a single grouped question (AskUserQuestion) or a short exchange. Collect:

- **project_name** (default: folder name) and **author** (default: `git config user.name`)
- **description** (one line)
- **ui_base_url** — the app under test
- **login selectors** — username / password / submit / success. Offer the
  defaults (`#UserName`, `#Password`, `input[type=submit]`, blank) and only ask
  the user to change them if their form differs. If unsure, drive the app live
  with Playwright MCP to read the real selectors first.
- **include_api** (bool) and, if yes, **api_base_url**
- **jira_base_url** / **jira_email** (optional, for the verify-ticket skill)

Do NOT ask for the username's password.

### 3. Write the config file and run

Write the collected answers to `bootstrap.json` (no password field). Preview
first with `--dry-run` (writes nothing) and show the user the planned changes:

```bash
uv run python bootstrap.py --config bootstrap.json --no-password --dry-run
```

Once they confirm, apply it:

```bash
uv run python bootstrap.py --config bootstrap.json --no-password --yes
```

`--yes` auto-confirms the clean git reset. Drop `--yes` (and warn the user) if
they want to keep existing history, or add `--no-git-reset`.

Example `bootstrap.json`:

```json
{
  "project_name": "Orders QA",
  "author": "Jane Smith",
  "description": "Orders app test automation",
  "ui_base_url": "https://orders.example.com",
  "username": "qa_user",
  "login_username_selector": "#email",
  "login_password_selector": "#password",
  "login_submit_selector": "button[type=submit]",
  "login_success_selector": "#dashboard",
  "include_api": true,
  "api_base_url": "https://orders.example.com/api",
  "jira_base_url": "",
  "jira_email": ""
}
```

Delete `bootstrap.json` afterward (it's scratch), or leave it — it holds no
secret.

### 4. Confirm and hand off

- Report what the script did (renamed project, wrote `.env`, generated the
  starter test, installed deps, reset git, verified collection).
- Tell the user the remaining manual step: **add `QA_PASSWORD=...` to `.env`**.
- Offer to write their first real test with the `write-ui-test` skill.

## Common Mistakes

- Handling the password in any form — don't. `--no-password`, always.
- Running in the Vexa framework repo instead of the user's clone.
- Skipping the live selector check when the user isn't sure of their form's
  selectors, then writing wrong values into `.env`.
