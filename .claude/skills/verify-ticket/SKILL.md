---
name: verify-ticket
description: Use when verifying a tracker ticket (Jira/Azure DevOps/GitHub issue) against the app in this Vexa repo — reproducing a reported bug or confirming a fix, capturing evidence screenshots, writing a Playwright test, and posting the verdict. Triggers include "verify ABC-123", "check this ticket", "is ABC-123 fixed", "reproduce this bug", "automate ABC-123".
---

# Verify a Ticket

## Overview

End-to-end workflow this repo repeats for every tracker ticket: understand the
ticket, verify it live in the app on the right environment, capture annotated
evidence, back it with an automated pytest test, and post a verdict on the
tracker with the evidence attached. The deliverable is always **a reproducible
verdict backed by proof** — screenshots + a passing test + a comment, not just
an opinion.

Read `CLAUDE.md` in the repo root first — it defines the architecture, the
authentication flow, and the gotchas this skill builds on.

## The Workflow

Track these as todos; do them in order.

### 1. Understand the ticket — read AND watch everything

- Fetch the ticket (tracker MCP/API, or the browser).
- **Pull and watch/open every attachment — video and screenshots — before
  forming a verdict.** Text repro alone misses key facts; attachments show the
  exact error, the exact screen, and the real precondition.
- Extract: the bug, the *expected* behavior, the acceptance criteria, the
  environment it was reported on, and the **fix scope** (which exact case the
  dev fixed — not a broader claim you can't back).

### 2. Pick the environment — ask if unclear

Apps often have multiple environments (dev/QA/staging) with different URLs and
sometimes different login flows. If the ticket doesn't pin one, **ask the user
which environment** before you start. Set `UI_BASE_URL` (and credentials)
accordingly in `.env`.

### 3. Verify live in the app

Reproduce the precondition and exercise the exact behavior the ticket describes.
Drive interactively with Playwright MCP (headed) to explore and confirm the
selectors and flow — some screens don't render reliably headless.

- Match the ticket's precondition exactly (right state, right data, right flag).
  A wrong precondition invalidates the verdict.
- Native `alert()`/`confirm()` dialogs are OS-level and **not screenshot-able**;
  capture their text with a `page.on("dialog", ...)` listener and quote it.
- Note any feature flags, missing endpoints/500s, or absent menus — these are
  common "feature not deployed on this environment" blockers.

### 4. Capture evidence with `annotated_step`

Use `utils.evidence.Evidence`. **Every** screenshot should go through
`annotated_step` so it carries the step text, the expected result, and a red
outline around the element under test:

```python
from utils.evidence import Evidence

evidence = Evidence(request.node.name)
evidence.scenario(
    "ABC-123 — <short title>",
    "<one-paragraph description of what this scenario verifies>",
    criteria=["<acceptance criterion 1>", "<criterion 2>"],
)
evidence.annotated_step(
    page,
    "Did X to element Y",
    expected="Y is in the expected state before the action under test.",
    box_locator=some_page.target_locator(),  # gets the red outline
)
# ... one annotated_step per meaningful action ...
evidence.write()  # writes steps.md (do this in a fixture teardown)
```

`Evidence` writes to `reports/evidence/<test-name>/` (nested under the ticket id
when the test is marked `@pytest.mark.ticket(...)`). For report content the
browser never shows on-screen (a downloaded .docx/PDF), render it to PNG and use
`image_step(png_bytes, description)`.

### 5. Write an automated test

One file per ticket: `tests/ui/test_<ticket>_<slug>.py`. Follow the example test
shape (`tests/ui/test_example_login.py`):

- Module docstring stating the bug, expected behavior, fix scope, environment,
  and a "verified live on <date>" line.
- `@pytest.mark.ui` **and** `@pytest.mark.ticket("ABC-123")`.
- Use the `uiLibrary` fixture and the `evidence` fixture.
- Log in via `uiLibrary.open_application(headless=True)` +
  `uiLibrary.login_with_credentials()`.
- Put locators/actions in a page object under `pages/ui/`; keep the test at the
  scenario level. Assertions carry a message that prints the observed state.
- The final assertion checks the authoritative server state (reload the screen),
  not just the optimistic in-page result.

Run it and get a real PASS:

```bash
uv run pytest tests/ui/test_<ticket>_<slug>.py -m ui
```

If it can't run headless (known quirk on some screens), say so plainly in the
evidence and rely on the live/headed verification — do not claim an unverified
PASS. Report failures with the actual output.

### 6. Write the evidence summary

Add `reports/evidence/<ticket>/EVIDENCE.md`: story/environment/date header, a
results table (item | result | ✅/⚠️/❌), the core finding with quoted dialog
text, and links to related tickets/evidence instead of duplicating screenshots.

### 7. Post the verdict

- Attach evidence files to the ticket (a tracker MCP, the tracker's API, or
  `utils/jira_attach.py` if present — reads `JIRA_EMAIL`/`JIRA_API_TOKEN` from
  `.env`).
- Post the comment via the tracker's MCP/API.
- **Write the comment in a direct, human voice** — no AI-isms, no generic
  transitions ("Additionally", "It's worth noting"), varied sentence length.
  State what you did, what you saw, and the verdict.

## Verdict Discipline

- Verify the fix's actual scope — not a case the dev didn't touch.
- If a feature is absent / behind a flag / 500s on this environment, that's the
  finding; don't force a PASS.
- Evidence before assertions: a claim of "fixed/passing" needs the screenshots
  and the test output behind it. A still-broken feature must not report PASS —
  assert the expected behavior and mark `xfail(strict=True)` so it shows XFAIL
  now and hard-fails (XPASS) when the fix lands.

## Common Mistakes

- Verdict before watching the ticket's video/screenshots.
- Wrong precondition (wrong state, flag off, missing data).
- Plain `step()` instead of `annotated_step` — evidence loses the caption/outline.
- Running against the wrong environment because you didn't ask.
- Claiming PASS from an optimistic in-page result instead of reloading server state.
- AI-flavored tracker prose.
