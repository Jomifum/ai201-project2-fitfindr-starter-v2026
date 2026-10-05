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
