## Capstone

**What This Extends**
Extended the FitFindr AI assistant system by adding input validation, failure containment for API keys and rate limits, unexpected exception handling, and a 15-field structured JSONL run logging module (`run_log.py`).

**The Shape**
Shape B — Harden against failure. Out of scope: rewriting prompt templates, modifying core UI/CLI interface code, and multi-model routing.

*Declared Stretch Goal:* Latency breakdown (measuring per-stage timing across runs from `runs_cost.jsonl`).

**Running It**
Path B — Local with logs. See `RUNNING.md` for the single start command, Python 3.12.10 environment specifications, and pinned dependencies (`requirements.txt`).

**Instrumentation**
Every run writes a JSON record with 15 named fields (`ts`, `run_id`, `query`, `model`, `outcome`, `error_type`, `error_message`, `selected_item_id`, `fit_card`, `duration_s`, `stage_durations_s`, `model_calls`, `prompt_tokens`, `output_tokens`, `cache_hits`) to `results/capstone/runs_cost.jsonl` via `run_log.py` (`write_run()`).

*Successful Run Log Entries (10 real entries from `results/capstone/runs_cost.jsonl`):*
<!-- PASTE ALL 10 LINES FROM results/capstone/runs_cost.jsonl HERE -->

*Failed Run Log Entries (from `results/capstone/runs_failures_retry.jsonl`):*
{"ts":"2026-11-18T00:07:15.142915-05:00","run_id":"dfb24c71-b0c2-42c9-a880-42bee8f196e3","query":"","model":"gemini-3.5-flash-lite","outcome":"bad_input","error_type":null,"error_message":"Type what you're looking for, for example 'vintage graphic tee under $30'.","selected_item_id":null,"fit_card":null,"duration_s":0.000148,"stage_durations_s":{},"model_calls":0,"prompt_tokens":0,"output_tokens":0,"cache_hits":0}
{"ts":"2026-11-18T00:07:15.144928-05:00","run_id":"41af7913-228a-4f97-af4f-984670bc0003","query":"under $30","model":"gemini-3.5-flash-lite","outcome":"bad_input","error_type":null,"error_message":"Your search had no item words. Add what you're looking for, for example 'denim jacket', plus a size or price if you like.","selected_item_id":null,"fit_card":null,"duration_s":0.000735,"stage_durations_s":{"parse":0.000616},"model_calls":0,"prompt_tokens":0,"output_tokens":0,"cache_hits":0}

**What It Costs**
10 measured runs on `gemini-3.5-flash-lite` consumed 15,454 prompt tokens and 3,128 output tokens, costing **$0.01245620** total.
*   **Total 10-run formula:** `(15,454 / 1,000,000 * $0.30) + (3,128 / 1,000,000 * $2.50) = $0.00463620 + $0.00782000 = $0.01245620`
*   **Per-run cost:** `$0.01245620 / 10 = $0.00124562` per run
*   **100-a-day arithmetic:** `$0.00124562 * 100 runs/day = $0.124562/day` (approximately **$0.125/day**).

*Latency Breakdown (Stretch — measured from `results/capstone/runs_cost.jsonl`):*
| Stage | Mean (s) | Min (s) | Max (s) | Share |
| :--- | :--- | :--- | :--- | :--- |
| Parse | 0.0005 | 0.0005 | 0.0006 | < 1% |
| Search | 2.27 | 1.80 | 3.71 | ~20% |
| Suggest (`suggest_outfit`) | 6.53 | 2.79 | 11.20 | ~59% |
| Fit Card (`create_fit_card`) | 2.21 | 1.24 | 4.89 | ~20% |

The **`suggest_outfit` stage dominates total latency**, averaging 6.53 seconds (~59% of end-to-end runtime).

**Run Log and Verdicts**
| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Empty/keywordless input rejection | Actionable error, 0 tool calls (4/4) | 4/4 | 4/4 | 4/4 | MET |
| 2. API-key/retry failure containment | Clean exit, 0 subsequent stages (4/4) | 4/4 | 4/4 | 4/4 | MET |
| 3. Unexpected stage exception handling | Caught exception, `--trace` tip (4/4) | 4/4 | 4/4 | 4/4 | MET |
| 4. Structured JSONL run logging | 15-field JSONL log, 0 secrets (5/5) | 5/5 | 5/5 | 5/5 | MET |
| 5. Matching query consistency | Selected item ID passed cleanly (5/5) | 5/5 | 5/5 | 5/5 | MET |

*Sample Real Output by Criterion:*
*   **C1 (`agent.py` → `run_agent()`):** `outcome="bad_input"`, `model_calls=0`, `error_message="Your search had no item words..."`
*   **C2 (`agent.py` → `_run_agent()` / `capstone_eval.py`):** `outcome="no_key"`, `create_fit_card=0`, `model_calls=0`
*   **C3 (`agent.py` → `_run_agent()`):** `outcome="unexpected_error"`, caught injected stage exception and printed `--trace` tip.
*   **C4 (`run_log.py` → `write_run()`):** Verified 15/15 JSONL fields present and 0 API-key strings in `results/capstone/before_c4_runs.jsonl`.
*   **C5 (`agent.py` → `run_agent()`):** `outcome="ok"`, `selected_item_id="lst_002"` passed intact into `create_fit_card`.

*Diagnosis:*
All 5 criteria met their targets across all three runs. Evaluating target tightness: **Criterion 1** was set too low because it only tested 4 basic empty/keywordless inputs and did not test whitespace-only or control-character edge cases. A tighter target is: **"5/5 empty, keywordless, or whitespace-only inputs (including tabs/newlines like `'   \t\n  '`) return `outcome='bad_input'` with 0 tool calls and 0 model calls."** Additionally, **Criterion 2** had the least margin because `suggest_outfit` is the stage that raises and catches the key error (`suggest_outfit: 1`), making the phrase "0 subsequent stages" ambiguous unless explicitly bounded at `create_fit_card == 0`.

**The Improvement**
Based on the Criterion 2 diagnosis, I updated `capstone_eval.py` to explicitly assert `create_fit_card == 0` at the true post-failure boundary (since `suggest_outfit` is where the missing-key error is raised and caught) and re-ran the full 5-criterion evaluation across 3 trials.

*Run Log — After:*
| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Empty/keywordless input rejection | Actionable error, 0 tool calls (4/4) | 4/4 | 4/4 | 4/4 | MET |
| 2. API-key/retry failure containment | Clean exit, 0 subsequent stages (4/4) | 4/4 | 4/4 | 4/4 | MET |
| 3. Unexpected stage exception handling | Caught exception, `--trace` tip (4/4) | 4/4 | 4/4 | 4/4 | MET |
| 4. Structured JSONL run logging | 15-field JSONL log, 0 secrets (5/5) | 5/5 | 5/5 | 5/5 | MET |
| 5. Matching query consistency | Selected item ID passed cleanly (5/5) | 5/5 | 5/5 | 5/5 | MET |

*Did it help?* Yes. Aligning the harness assertion with the actual failure boundary eliminated the ambiguity in Criterion 2's measurement without loosening the target, confirming 4/4 containment across all three after-runs with no regressions in C1, C3, C4, or C5.

**What's Still Broken**
All 5 criteria met their targets. As diagnosed above, Criterion 1's target was set too low and should be tightened to **5/5 including whitespace-only/control-character inputs returning `bad_input` with 0 tool calls**.

*What I would do first with another unit:* I would separate `error_message` (user-facing text) from a new `raw_error` field (`str(exc)`) inside `agent.py` (`run_agent()`). Right now, unexpected exceptions store `str(exc)` and then immediately overwrite it with the user-facing message, which destroys the raw debugging cause in the JSONL log. Fixing this first gives the highest return on observability for diagnosing real production crashes.

**How I Used AI**
1. **Generating the Harness:** Asked AI to build `capstone_eval.py`; it mapped my 5 criteria into 66 standalone offline trials with stage wrappers and secret redaction. I reviewed and adjusted the C2 boundary assertion to match `agent.py`.
2. **Diagnosing the Margin:** Asked AI to audit the saved run records against `criteria.md` without editing code; it identified the C2 wording ambiguity (`suggest_outfit: 1` vs. `create_fit_card: 0`) and flagged that `runs_cost.jsonl` had 15 fields including `model`.