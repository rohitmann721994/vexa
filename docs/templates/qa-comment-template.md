# QA Verdict Comment Template

Used at the end of `verify-ticket`'s workflow (step 7, "Post the verdict") to
keep tracker comments consistent across tickets — same shape every time, so a
reviewer can scan it in seconds, but never a copy-paste of AI-flavored prose.

**Write in a direct, human voice.** No AI-isms ("It's worth noting...",
"Additionally...", "I hope this helps"), no generic transitions, no restating
the ticket title back at the reporter. State what you did, what you saw, and
the verdict. Vary sentence length. Cut anything that doesn't change the
reader's next action.

## Template

```markdown
**Verified on:** <environment> — <YYYY-MM-DD>
**Build/commit:** <version, deploy tag, or commit SHA if known>

**What I did:** <one or two sentences — the precondition you set up and the
exact action you took, matching the ticket's repro steps>

**What I saw:** <one or two sentences — the actual behavior, quoting any
dialog/error text verbatim. If a screen didn't render, say so instead of
guessing.>

**Result:** ✅ Fixed / ⚠️ Partially fixed / ❌ Still broken / 🚫 Blocked
<one line qualifying the result — e.g. which case is fixed vs. still open,
or what's blocking verification (feature flag, missing endpoint, wrong env)>

**Evidence:** <link(s) to attached screenshots/video, and the automated test
path, e.g. `tests/ui/test_ABC-123_login_error.py`>

**Test run:**
\`\`\`
<the actual pytest output line — PASS/FAIL/XFAIL, not a paraphrase>
\`\`\`
```

## Filled example

```markdown
**Verified on:** staging — 2026-08-05
**Build/commit:** deploy-2026-08-05-14

**What I did:** Logged in as a standard user, opened Orders, and submitted an
order with an expired card to match the repro steps.

**What I saw:** The form now shows "Card expired — update payment details"
inline under the card field instead of the blank 500 page from the ticket.
Reloading the page keeps the order in "Payment failed" status, so the error
isn't just an optimistic in-page message.

**Result:** ✅ Fixed — the exact case in the ticket (expired card on
checkout) is resolved. Didn't test other decline reasons (insufficient
funds, etc.); those weren't in scope for this ticket.

**Evidence:** screenshots attached above; test at
`tests/ui/test_ABC-123_expired_card_checkout.py`

**Test run:**
\`\`\`
tests/ui/test_ABC-123_expired_card_checkout.py::test_expired_card_shows_inline_error PASSED
\`\`\`
```

## Rules

- **Every field needs a real value pulled from your run** — no placeholder
  text left in, no field guessed instead of observed.
- **Result must match fix scope**, not a broader claim. If the ticket covers
  three cases and only one was verified, say which one.
- **Still-broken stays ❌**, backed by an `xfail(strict=True)` test (see
  `verify-ticket`'s Verdict Discipline) — never round a partial fix up to ✅.
- Skip the `Build/commit` line if you genuinely don't know it; don't fill it
  with a guess.
