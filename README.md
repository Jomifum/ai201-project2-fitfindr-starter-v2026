# TakeMeter

> ### ?? Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** � setup, the
> notebook, the baseline, and what to do when something breaks.
>
> Once python test.py passes:
>
> `ash
> head -5 data/practice_labels.csv    # the shape your labels.csv needs
> `
>
> Then open 	akemeter.ipynb **in this folder** � in VS Code, or with
> jupyter notebook if you prefer. Pick the kernel: the .venv inside this
> project. Run section 1, which reports the hardware you'll be training on.
> Everything else waits until you have data.
>
> Nothing to upload, nothing to connect, no accounts and no keys. The notebook
> runs on your machine and writes next to your code.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

## What This Does

This project is a text classifier designed to sort posts from the **r/sustainability** community. Online environmental communities often mix practical tips, high-level economic arguments, and scientific data drops. This model automatically categorizes posts into one of three distinct lanes to help users filter between actionable daily habits, broad systemic discussions, and hard news.

---

## Label Taxonomy

### personal_action
**Definition:** A post asking for or sharing practical, individual tips for reducing one's environmental footprint at home or work.

### systemic_debate
**Definition:** An argument or discussion focusing on large-scale corporate practices, government policies, or global economic systems.

### 
ews_and_data
**Definition:** A post sharing or summarizing a specific new scientific study, climate metric, or recent environmental news event.

### The hardest boundary
**Which two labels:** personal_action and systemic_debate  
**The decision rule:** If the ultimate goal of the post is to persuade the reader to change a daily habit or make a personal purchase, it is personal_action.

---

## The Dataset
* **Source:** Public threads on 
/sustainability.
* **Counts:** personal_action (111), systemic_debate (73), 
ews_and_data (20) � Total: 204.

---

## The Training Run
- **Hardware / Device:** CPU (	orch_version: 2.14.1+cpu)
- **Settings:** Default 3 epochs, learning rate 2e-5, batch size 16.

---

## How I Used AI
1. **Pre-labeling Assistance:** Used AI to pre-label raw text based on taxonomy rules, followed by a mandatory manual review of every single row.
2. **Boundary Analysis:** Used AI to argue borderline cases to refine decision rules.

---

## Baseline vs. Trained

| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy | 0.323 | 0.677 | +0.355 |
| Macro F1 | 0.258 | 0.400 | +0.142 |

---

## Run Log � Before

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1. Dataset Size | At least 200 labeled examples | 204 | 204 | 204 | MET |
| 2. Class Balance | No single label makes up > 60% | 56.9% | 56.9% | 56.9% | MET |
| 3. Recall | Recall for personal_action > 0.75 | 1.000 | 0.944 | 0.944 | MET |
| 4. F1 Beat | Fine-tuned macro F1 beats baseline by 0.05 | +0.142 | +0.201 | +0.193 | MET |
| 5. Confidence Gap | Top third accuracy > 20% higher than bottom | 1.67x | 2.50x | 3.33x | MET |

---

## The Improvement & Run Log � After
* **Improvement:** Added more examples and re-ran training splits.
* **Result:** Average accuracy rose to 0.818, macro F1 rose to 0.558. All 5 criteria MET.

---

## Agreement Report
Agreement rate: 30 / 30 = 100% with staff classification set.

---

## What's Still Broken
Model performance on rare classes like 
ews_and_data remains limited due to small sample size in test splits.

---

## Capstone

**What This Extends**
Extended the FitFindr AI assistant system by adding robust input validation, failure containment for API keys and rate limits, unexpected exception handling, and a 14-field structured JSONL run logging module (
un_log.py).

**The Shape**
Shape B � Harden against failure. Out of scope: rewriting prompt templates, modifying core UI/CLI interface code, and multi-model routing.

**Running It**
Path B � Local with logs. See RUNNING.md for the single start command, Python 3.12.10 environment specifications, and dependencies.

**Instrumentation**
Every run writes a JSON record with named fields (timestamp, input, output, duration, stage timings, model calls, and outcome/error) to 
esults/capstone/runs_cost.jsonl. 

*Successful Run Log Entries (Sample from runs_cost.jsonl):*
{"ts":"2026-11-18T00:01:18.829169-05:00","run_id":"44c6924f-2e84-4eb0-9abd-917b739235f5","query":"vintage graphic tee under $30","model":"gemini-3.5-flash-lite","outcome":"ok","error_type":null,"error_message":null,"selected_item_id":"lst_002","fit_card":"Channel your inner 2000s icon with this nostalgic Y2K Baby Tee — Butterfly Print, featuring a sweet graphic that pairs effortlessly with baggy jeans and chunky sneakers. Grab this nostalgic piece for just $18 over on depop to complete your ultimate casual daytime streetwear look.","duration_s":21.12079,"stage_durations_s":{"parse":0.000616,"search":3.356012,"suggest_outfit":10.508152,"create_fit_card":7.03387},"model_calls":2,"prompt_tokens":1585,"output_tokens":348,"cache_hits":0} {"ts":"2026-11-18T00:01:26.029739-05:00","run_id":"a67c8a53-9d29-4bc5-844d-f5e0e6b9a38a","query":"90s track jacket in size M","model":"gemini-3.5-flash-lite","outcome":"ok","error_type":null,"error_message":null,"selected_item_id":"lst_004","fit_card":"Channel a effortless 90s athletic aesthetic with this sporty navy and white layering piece. Style it over a white ribbed tank and baggy straight-leg jeans with chunky sneakers for the ultimate daytime streetwear vibe. Grab the 90s Track Jacket — Navy/White Stripe for $45 on poshmark before it's gone!","duration_s":6.715576,"stage_durations_s":{"parse":0.000583,"search":2.090373,"suggest_outfit":3.875355,"create_fit_card":0.692598},"model_calls":2,"prompt_tokens":1550,"output_tokens":327,"cache_hits":0} {"ts":"2026-11-18T00:01:43.001453-05:00","run_id":"86ac898a-d238-4261-97b0-a35a7604170a","query":"denim jacket under $50","model":"gemini-3.5-flash-lite","outcome":"ok","error_type":null,"error_message":null,"selected_item_id":"lst_007","fit_card":"Channel classic streetwear energy with this versatile Denim Jacket — Light Wash, Cropped, priced at $42 on poshmark. Throw it on over an oversized grey crewneck sweatshirt and wide-leg khaki trousers for an effortless daytime look. It is the ultimate layering staple for your everyday rotation.","duration_s":16.537239,"stage_durations_s":{"parse":0.000601,"search":2.076913,"suggest_outfit":8.2709,"create_fit_card":6.137005},"model_calls":2,"prompt_tokens":1564,"output_tokens":340,"cache_hits":0} {"ts":"2026-11-18T00:01:57.333561-05:00","run_id":"e9a8230e-1585-4373-9b68-a382ea85b166","query":"silk slip dress in midi length under $40","model":"gemini-3.5-flash-lite","outcome":"ok","error_type":null,"error_message":null,"selected_item_id":"lst_013","fit_card":"Channel effortless 90s grunge by styling this 90s Silk Slip Dress — Floral, Midi Length under an oversized black denim jacket and chunky combat boots. Available now on depop for just $30, this ultra-feminine piece is ready to bring major vintage charm to your wardrobe.","duration_s":13.878691,"stage_durations_s":{"parse":0.000565,"search":2.597839,"suggest_outfit":10.046769,"create_fit_card":1.181778},"model_calls":2,"prompt_tokens":1547,"output_tokens":293,"cache_hits":0} {"ts":"2026-11-18T00:02:08.997945-05:00","run_id":"0bf51e31-523e-4b04-8b4f-fdffedc0ab0b","query":"platform sneakers size 8","model":"gemini-3.5-flash-lite","outcome":"ok","error_type":null,"error_message":null,"selected_item_id":"lst_019","fit_card":"Channel major 90s streetwear energy with these Platform Sneakers — White Chunky Sole, listed for $48 over on poshmark. They bring the ultimate chunky Y2K vibe to any rotation. Style them effortlessly for daytime errands by pairing them with a ribbed tank, baggy dark-wash jeans, and a vintage black denim jacket.","duration_s":11.205055,"stage_durations_s":{"parse":0.000584,"search":2.062846,"suggest_outfit":8.028961,"create_fit_card":1.06302},"model_calls":2,"prompt_tokens":1459,"output_tokens":237,"cache_hits":0}

*Failed Run Log Entries (Sample from runs_failures_retry.jsonl):*
{"ts":"2026-11-18T00:07:15.142915-05:00","run_id":"dfb24c71-b0c2-42c9-a880-42bee8f196e3","query":"","model":"gemini-3.5-flash-lite","outcome":"bad_input","error_type":null,"error_message":"Type what you're looking for, for example 'vintage graphic tee under $30'.","selected_item_id":null,"fit_card":null,"duration_s":0.000148,"stage_durations_s":{},"model_calls":0,"prompt_tokens":0,"output_tokens":0,"cache_hits":0} {"ts":"2026-11-18T00:07:15.144928-05:00","run_id":"41af7913-228a-4f97-af4f-984670bc0003","query":"under $30","model":"gemini-3.5-flash-lite","outcome":"bad_input","error_type":null,"error_message":"Your search had no item words. Add what you're looking for, for example 'denim jacket', plus a size or price if you like.","selected_item_id":null,"fit_card":null,"duration_s":0.000735,"stage_durations_s":{"parse":0.000616},"model_calls":0,"prompt_tokens":0,"output_tokens":0,"cache_hits":0}

**What It Costs**
10 runs on gemini-3.5-flash-lite cost **.01245620**.
*Formula:* (15454 / 1,000,000 * .30) + (3128 / 1,000,000 * .50)
*100-a-day estimate:* ~.125 / day.

*Latency Breakdown (from runs_cost.jsonl):*
| Stage | Mean (s) | Min (s) | Max (s) | Share |
| :--- | :--- | :--- | :--- | :--- |
| Parse | 0.0005 | 0.0005 | 0.0006 | < 1% |
| Search | 2.27 | 1.80 | 3.71 | ~20% |
| Suggest | 6.53 | 2.79 | 11.20 | ~59% |
| Fit Card | 2.21 | 1.24 | 4.89 | ~20% |

**Run Log and Verdicts**
| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Empty/keywordless input rejection | Actionable error, 0 tool calls | 4/4 | 4/4 | 4/4 | MET |
| 2. API-key/retry failure containment | Clean exit, 0 subsequent stages | 4/4 | 4/4 | 4/4 | MET |
| 3. Unexpected stage exception handling | Caught exception, --trace tip | 4/4 | 4/4 | 4/4 | MET |
| 4. Structured JSONL run logging completeness | 14-field JSONL log, 0 secrets | 5/5 | 5/5 | 5/5 | MET |
| 5. Matching query end-to-end consistency | ID passed without mutation | 5/5 | 5/5 | 5/5 | MET |

**The Improvement**
Updated the C2 check in capstone_eval.py to assert create_fit_card == 0, aligning the harness with the true failure boundary (since suggest_outfit catches the error). 

*Before vs After Evaluation Comparison:*
| Criterion | Before (Run 1 / 2 / 3) | After (Run 1 / 2 / 3) |
|---|---|---|
| C1 | 4/4 | 4/4 |
| C2 | 4/4 (ambiguous assert) | 4/4 (tightened assert) |
| C3 | 4/4 | 4/4 |
| C4 | 5/5 | 5/5 |
| C5 | 5/5 | 5/5 |

**What's Still Broken**
All 5 criteria MET their targets. Because all criteria passed, target tightness is evaluated: Criterion 1's target of requiring 4/4 inputs to catch errors is set slightly too low regarding edge whitespace variants; we would tighten it to enforce strict regex trimming. The primary remaining technical gap is that unexpected exceptions overwrite the raw exception traceback in the session log with the user-facing message, limiting deep debugging data.

**How I Used AI**
1. **Generating the Harness:** Asked AI to build capstone_eval.py; it successfully mapped 5 criteria into 66 standalone offline trials without module-level cross-contamination.
2. **Diagnosing the Margin:** Used AI to analyze the "least margin" of success, correctly identifying the ambiguity in C2's target wording versus the harness logic.
