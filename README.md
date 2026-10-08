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

<!-- TODO: Before submission, choose two candidates and replace them with your
     own account of what you asked, what came back, and what you changed. -->

**Candidate 1: Query parser**

- *What I asked for:* Add a `parse_query` helper for price and size phrases.
- *What came back:* Three checks parsed `vintage graphic tee under $30`, `neon tuxedo under $2, size XXS`, and `black jeans` into the expected filters and descriptions.
- *What I changed:* Added the helper in `agent.py` and committed it as `1281685`.

**Candidate 2: Empty-search branch**

- *What I asked for:* Implement the session-backed planning branch and make the no-match message actionable.
- *What came back:* The real search value for `neon tuxedo under $2, size XXS` was `[]`; the CLI then named the keywords, size, and price ceiling to change.
- *What I changed:* Implemented the tool sequence and early return in `run_agent`, committed as `c670d68`.

**Candidate 3: Model errors and session debug**

- *What I asked for:* Catch `ModelUnavailable` from both model-backed tools and print the final session with an item-identity check.
- *What came back:* The happy path printed `Selected item ID matches suggest_outfit input: True`; mocked failures from both tools returned error sessions.
- *What I changed:* Added both catches and the session debug view in `agent.py`, committed as `09d52dc`.

**TODO for me:** Replace two candidate entries with my own account of what I asked, what came back, and what I changed.

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
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

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

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



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

```

**Empty search**

```

```

### MCP Move

Moved `search_listings` onto MCP. `mcp_server.py` registers the wrapper,
`mcp_client.py::call_tool` makes the request and unwraps its value, and
`agent.py::run_agent` now uses that client for search. With `description`
`graphic tee`, `size` `L`, and `max_price` `24`, both calls returned equal
`list[dict]` values: `lst_006` at `24.0` and `lst_033` at `19.0`. There was no
difference in type, shape, or field values; prices remained floats.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



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
