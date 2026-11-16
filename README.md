# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

Ask FitFindr for a secondhand clothing item, with optional size and price-limit phrases such as `size M` or `under $30`. It searches the bundled listings by keyword overlap, filters by size and price, and selects the highest-ranked match. The model suggests outfits using the saved wardrobe, or general styling advice if it is empty, then writes a postable fit-card caption. If nothing matches, FitFindr explains which keywords or filters to loosen.



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Finds listings by case-insensitive keyword overlap between the query and each listing's title, description, category, style tags, and brand; split text into lowercase alphanumeric terms, score by the number of distinct query terms found, and preserve source order on ties. Apply optional size and price filters, then return the highest-scoring matches up to `SEARCH_RESULT_LIMIT`.
- **Inputs:** `description` (`str`); `size` (`str | None`); `max_price` (`float | None`, inclusive).
- **Returns:** A `list[dict]` of listing records with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`, ordered by match score. `brand` may be `None`.
- **When it has nothing:** Return `[]` if no listing matches the query and filters. Size matching is case-insensitive by whole size token: `M` matches `S/M`, but `L` does not match `XL`.

### `suggest_outfit`

- **What it does:** Suggests one or two outfits built around the selected listing, using pieces from the user's wardrobe when available.
- **Inputs:** `new_item` (`dict`, a listing record); `wardrobe` (`dict` with an `items` list of wardrobe-item dicts).
- **Returns:** A non-empty `str` containing one or two outfit suggestions; with wardrobe items, suggestions name pieces the user owns.
- **When it has nothing:** If `wardrobe["items"]` is empty, return general styling advice for the listing as a non-empty string, not an error or empty string.

### `create_fit_card`

- **What it does:** Writes a short, post-ready caption for the selected listing and its outfit suggestion.
- **Inputs:** `outfit` (`str`, from `suggest_outfit`); `new_item` (`dict`, a listing record).
- **Returns:** A `str` of two to four sentences that mentions the item, its price, and its platform once each, and describes its vibe.
- **When it has nothing:** If `outfit` is empty or whitespace, return a non-empty descriptive fallback for the listing instead of raising.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns `[]`, store an actionable message in `session["error"]` naming the query terms and any supplied size or price ceiling, then return without calling either model-backed tool. Otherwise, store the first ranked result in `session["selected_item"]`, call `suggest_outfit` with that item, and call `create_fit_card` with the stored outfit and item. If either model-backed tool raises `ModelUnavailable`, store an error and return the session.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** `parse_query` uses case-insensitive regular expressions to extract `under $30` or `below 30` as a float price ceiling, and `size M` or `size XXS` as an uppercase size. It removes those phrases and leftover separators; the remaining text is the keyword description.

**What moves through the session:** `query` is parsed into `parsed` (`description`, `size`, `max_price`). `search_listings` receives those stored values and its list is stored in `search_results`. The first result is stored in `selected_item`; `suggest_outfit` receives that session item and `wardrobe`, and its output is stored in `outfit_suggestion`. `create_fit_card` reads the stored item and outfit and stores its result in `fit_card`. `error` records an early stop or model failure.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
Selected item ID matches suggest_outfit input: True
Final session debug (key fields): `query='vintage graphic tee under $30'`, `parsed.description='vintage graphic tee'`, `parsed.max_price=30.0`, `selected_item.id='lst_002'`, `error=None`.

     Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

     Outfit:   Here are two wearable outfits centered on your **Y2K Baby Tee — Butterfly Print**:

### Outfit 1: Y2K Streetwear (Casual daytime)
*   **Top:** Y2K Baby Tee — Butterfly Print
*   **Bottoms:** Baggy straight-leg jeans, dark wash (paired with the Brown leather belt)
*   **Outerwear:** Black cropped zip hoodie
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag
*   **Why it works:** The fitted, cropped baby tee contrasts sharply with the high-waisted, baggy dark indigo jeans for an authentic early-2000s silhouette. Layering the black cropped zip hoodie on top keeps the midriff balanced while playing into streetwear proportions.

### Outfit 2: Edgy Contrast (Weekend errands or casual hangouts)
*   **Top:** Y2K Baby Tee — Butterfly Print
*   **Bottoms:** Wide-leg khaki trousers (paired with the Brown leather belt)
*   **Outerwear:** Vintage black denim jacket
*   **Shoes:** Black combat boots
*   **Accessories:** Black crossbody bag
*   **Why it works:** The pink and purple butterfly graphic pops against the neutral tan trousers. Tying the vintage black denim jacket and black combat boots into the look grounds the sweet cottagecore/Y2K vibe with classic grunge elements.

     Fit card: Channel early-2000s streetwear energy with this sweet Y2K Baby Tee — Butterfly Print, available now for $18. Pair it with baggy dark wash jeans and chunky white sneakers for the ultimate casual daytime look. Grab it exclusively on depop before it's gone!

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
Command: .\.venv\Scripts\python.exe -c "from tools import search_listings; print([(item['id'], item['price']) for item in search_listings('graphic tee', max_price=30)])"
Output: [('lst_002', 18.0), ('lst_006', 24.0), ('lst_017', 15.0), ('lst_033', 19.0), ('lst_011', 27.0), ('lst_015', 26.0)]
```

```
Command: .\.venv\Scripts\python.exe -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; advice=suggest_outfit(load_listings()[0], get_empty_wardrobe()); assert advice.strip(); print(advice.splitlines()[0])"
Output: Here are two wearable, occasion-specific outfit suggestions built around your vintage Levi's 501s, using classic hypothetical basics.
```

```

Command: .\.venv\Scripts\python.exe -c "from tools import create_fit_card; from utils.data_loader import load_listings; item=load_listings()[0]; outfit='white tee, olive chore jacket, white sneakers'; [print(create_fit_card(outfit, item)) for _ in range(3)]"
Output:
Grab these Vintage Levi's 501 Jeans — Medium Wash on depop for $38 to nail that effortless streetwear vibe. Style them with a crisp white tee, an olive chore jacket, and clean white sneakers for an easy, classic look.
Grab these Vintage Levi's 501 Jeans — Medium Wash on depop for $38 to nail that effortless streetwear vibe. Style them with a crisp white tee, an olive chore jacket, and clean white sneakers for an easy, classic look.
Grab these Vintage Levi's 501 Jeans — Medium Wash on depop for $38 to nail that effortless streetwear vibe. Style them with a crisp white tee, an olive chore jacket, and clean white sneakers for an easy, classic look.
```

The three fit cards were identical because `CACHE_ENABLED=True`; `TEMPERATURE=0.9`.

---

## How I Used AI

**Moment 1: Long evaluation output**

- *What I asked:* Inspect the after-run output and find the scenario results.
- *What came back:* The terminal output exceeded the read limit (73 KB); the full text was saved separately.
- *What changed:* I read the saved report in smaller sections instead of relying on the truncated terminal view.

**Moment 2: Model-unavailable test**

- *What I asked:* Verify a bad-key request failed cleanly without a cache hit or stack trace, then restore the key.
- *What came back:* The first command response only confirmed the temporary one-character change; after restoring the backup, `test.py` passed 10/10. Inspection of the captured CLI output showed one model call, no cache hit, and the handled model-unavailable message.
- *What changed:* I verified the saved CLI output and reran the environment/model check after restoring the backup; I did not change application code for this test.

**Moment 3: C1 diagnostic rerun**

- *What I asked:* Add assertion-specific details to C1 and rerun that scenario five times.
- *What came back:* All five diagnostic tries passed; each had one MCP search, one outfit call, one card call, a truthy card, and no session error.
- *What changed:* I added diagnostic assertion messages in `scenarios.py` and saved `results/diagnostic_c1.md` in commit `4f49983`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes | At least 4/5 complete all three tools and return a fit card | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops early | 5/5 stop before `suggest_outfit` and return a message naming what to change | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item reaches the next tool | 5/5 selected IDs match the IDs actually passed to `suggest_outfit` | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit cards keep required details | With cache off and temperature > 0: five same-item/outfit cards; each 2–4 sentences with title, price, platform once; at least 3 distinct | PASS | PASS | PASS | PASS | PASS | MET (5/5; 4 distinct) |
| 5. Model failures return an error session | In 5/5 `ModelUnavailable` runs, return a session with non-empty `error` | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try per criterion** (recorded by `run_eval.py::run_once` in `results/run_2026-11-15_2123_before.md`):

```
C1 — `agent.py::run_agent`; fit card from `tools.py::create_fit_card`
[1] parse_query
     in:  vintage graphic tee under $30
     out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
     in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
     out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] branch
     in:  10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
     out: continue
     →    search results found
[4] suggest_outfit
     in:  item_id=lst_002, wardrobe_items=10
     out: Here are two specific, wearable outfits centered on the **Y2K Baby Tee — Butterfly Print**:  ### Outfit 1: Y2K…
[5] create_fit_card
     in:  item_id=lst_002, outfit=Here are two specific, wearable outfits centered on the **Y2K Baby Tee — Butterfly Pri…
     out: Channel serious 2000s energy with the Y2K Baby Tee — Butterfly Print, listed on depop for just $18. This fitte…
Fit card:
Channel serious 2000s energy with the Y2K Baby Tee — Butterfly Print, listed on depop for just $18. This fitted graphic top has a nostalgic streetwear vibe that looks effortless paired with baggy dark-wash jeans and chunky white sneakers. Grab it now to complete your vintage-inspired wardrobe rotation.

C2 — `agent.py::run_agent`
- session.error: No listings match 'neon tuxedo' in size XXS under $2. Try one of these changes: raise the price ceiling, try a different size or use broader keywords.
- stopped early: yes — No listings match 'neon tuxedo' in size XXS under $2. Try one of these changes: raise the price ceiling, try a different size or use broader keywords.
- selected_item: (none)
- search_results: 0

C3 — `agent.py::run_agent`; ID comparison in `scenarios.py::_run_with_criterion_checks`
- selected_item: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
- search_results: 3
[4] suggest_outfit
     in:  item_id=lst_006, wardrobe_items=10
Fit card:
Channel total grunge energy in this Graphic Tee — 2003 Tour Bootleg Style, available now on depop for $24. Layer it over a white ribbed tank with baggy jeans and chunky sneakers for an effortless streetwear vibe. Grab it before it's gone!

C4 — `tools.py::create_fit_card`, called by `agent.py::run_agent`
- selected_item: Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
- search_results: 2
Outfit suggestion:
a white tee, straight-leg jeans, and sneakers
Fit card:
Channel ultimate streetwear vibes in these Vintage Levi's 501 Jeans — Medium Wash, available on depop for just $38. This classic denim staple is begging to be styled with a white tee, straight-leg jeans, and sneakers for an effortlessly cool daily look. Grab this timeless piece today!

C5 — `agent.py::run_agent` with `suggest_outfit` mocked by `scenarios.py::_run_with_criterion_checks`
- session.error: The model couldn't be reached while suggesting an outfit. Check the API key in .env and your network connection, then retry.
[4] suggest_outfit
     in:  item_id=lst_004, wardrobe_items=10
     out: ModelUnavailable
     →    model unavailable
```

### Run Log — After

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
[1] parse_query
     in:  vintage graphic tee under $30
     out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
     in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
     out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] branch
     in:  10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
     out: continue
     →    search results found
[4] suggest_outfit
     in:  item_id=lst_002, wardrobe_items=10
     out: Here are two wearable outfits centered on your **Y2K Baby Tee — Butterfly Print**:  ### Outfit 1: Y2K Streetwe…
[5] create_fit_card
     in:  item_id=lst_002, outfit=Here are two wearable outfits centered on your **Y2K Baby Tee — Butterfly Print**:  ##…
     out: Channel early-2000s streetwear energy with this sweet Y2K Baby Tee — Butterfly Print, available now for $18. P…
```

**Empty search**

```
[1] parse_query
     in:  neon tuxedo under $2, size XXS
     out: description='neon tuxedo', size='XXS', max_price=2.0
[2] search_listings (via MCP)
     in:  {'description': 'neon tuxedo', 'size': 'XXS', 'max_price': 2.0}
     out: [] (empty)
[3] branch
     in:  [] (empty)
     out: stop
     →    empty search results
```

**On the MCP move:** TODO (me)

### Failure Modes

- **Empty search:** `No listings match 'neon tuxedo' in size XXS under $2. Try one of these changes: raise the price ceiling, try a different size or use broader keywords.` Handler: `agent.py::run_agent` returns from the empty-results branch before calling either model-backed tool.
- **Empty wardrobe:** The returned advice began: `Here are two specific outfit suggestions featuring the Y2K Butterfly Baby Tee, built using versatile wardrobe basics.` Handler: none needed; `tools.py::suggest_outfit` already gives general styling advice and has a non-empty fallback.
- **Model unavailable while suggesting an outfit:** `The model couldn't be reached while suggesting an outfit. Check the API key in .env and your network connection, then retry.` **While creating the fit card:** `The model couldn't be reached while creating the fit card. Check the API key in .env and your network connection, then retry.` Handler: `agent.py::run_agent` catches `ModelUnavailable`, stores the actionable message in `session["error"]`, and returns. The live model call succeeded; these handler messages were verified with mocked failures.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
