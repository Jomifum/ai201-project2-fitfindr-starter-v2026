# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I chose 4 of 5 rather than 5 of 5 because the search uses keyword matching, so an unusual phrasing can miss even when a relevant listing exists. The four-of-five target still requires the full tool sequence on most ordinary matching queries.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
For scoring, the message must name at least one query detail to change, such as the search terms, size, or price limit; a generic "no results" does not count. I chose 5 of 5 because detecting an empty result and returning early is deterministic and should not depend on a model response.

---

## 3. The selected item reaches the next tool

For 5 of 5 matching queries, the `id` in `session["selected_item"]` is the same as the `id` of the `new_item` actually passed to `suggest_outfit`.


**Why this target:**

The selected item is passed through the session, so its identity should be preserved every time; this is deterministic state handling, not variable model wording. Comparing IDs makes the result observable without judging the outfit text.



---

## 4. Fit cards keep required details

With `CACHE_ENABLED=False` and `TEMPERATURE > 0`, generate five fit cards from the same item and outfit. Every card is 2–4 sentences and mentions the listing's title, price, and platform exactly once each. At least three of the five output strings must be distinct.


**Why this target:**

I chose 5 of 5 for the item facts and sentence count because the tool receives the listing data needed for every card. Requiring three distinct strings shows the model can vary its wording without expecting all five generations to be unique.


---

## 5. Model failures return an error session

In 5 of 5 runs where `suggest_outfit` raises `ModelUnavailable`, `run_agent` returns a session with a non-empty `error` instead of letting the exception escape.


**Why this target:**

I chose 5 of 5 because a simulated model outage should follow the same error-handling path every time. Returning a session error lets the caller report the problem instead of crashing, while keeping this check independent of live service availability.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

## Capstone criteria (Unit 9)

## 1. Empty and keywordless query rejection
**Target:** Across 4 invalid inputs (`""`, `"   "`, `"under $30"`, and `"size M"`), 4/4 runs return a non-empty actionable `session["error"]` (`outcome: "bad_input"`) and invoke `search_listings` and `suggest_outfit` 0 times.
**Why this target:** Prevents wasted MCP and model calls on queries lacking searchable item words and gives the user a concrete correction message instead of empty results or a `TypeError`.

## 2. API-key and rate-retry failure containment
**Target:** Across 4 simulated failure runs—unset `GEMINI_API_KEY` (`no_key`), whitespace-only `GEMINI_API_KEY` (`no_key`), invalid `GEMINI_API_KEY` (`model_unavailable`), and `MAX_RETRIES` exhaustion—4/4 runs exit cleanly with 0 escaped exceptions, populate a normalized `session["error"]`, and execute 0 subsequent planning stages (`suggest_outfit` or `create_fit_card`).
**Why this target:** Ensures configuration mistakes and upstream quota/API failures degrade into deterministic session failures rather than unhandled tracebacks or partial tool execution.

## 3. Unexpected stage exception handling
**Target:** When `suggest_outfit` or `create_fit_card` raises an unexpected exception (`RuntimeError` or `KeyError`, tested across 4 runs, 2 per stage), 4/4 runs catch the exception at the agent boundary, set `session["error"]` naming the failing stage and `--trace` flag, and terminate the planning loop immediately.
**Why this target:** Protects CLI and HTTP callers from raw stack traces while preserving actionable diagnostic context about which planning stage failed.

## 4. Structured JSONL run logging completeness
**Target:** Across 5 test runs covering valid execution (`ok`), empty/keywordless input (`bad_input`), impossible search (`empty_search`), missing API key (`no_key`), and simulated stage exception, 5/5 runs append exactly 1 valid JSON object to the configured `FITFINDR_LOG` file containing all 14 schema fields (plus `model`), non-negative stage timings, accurate model call counts, and `outcome`/`error` matching the session with 0 secret values logged.
**Why this target:** Guarantees complete, auditable telemetry across every success and early-exit path without leaking credentials.

## 5. Matching query end-to-end consistency (baseline guard)
**Target:** Across 5 runs of the deterministic matching query `"vintage graphic tee under $30"`, 5/5 runs complete all three stages (`search_listings`, `suggest_outfit`, `create_fit_card`) with `outcome: "ok"`, pass the exact `session["selected_item"]["id"]` (`lst_002`) into `suggest_outfit` without mutation, and return a non-empty fit card.
**Why this target:** Confirms that the new input validation, exception containment, and structured logging wrappers preserve core end-to-end tool chaining and item selection integrity.
