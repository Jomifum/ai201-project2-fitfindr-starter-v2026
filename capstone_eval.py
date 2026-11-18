"""Criterion-driven Capstone evaluation. Run with `.venv\\Scripts\\python.exe capstone_eval.py`."""

import argparse
import contextlib
import copy
import io
import json
import os
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "capstone"
UNSET = object()
LOG_FIELDS = {
    "ts",
    "run_id",
    "query",
    "model",
    "outcome",
    "error_type",
    "error_message",
    "selected_item_id",
    "fit_card",
    "duration_s",
    "stage_durations_s",
    "model_calls",
    "prompt_tokens",
    "output_tokens",
    "cache_hits",
}


def _read_lines(path):
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def _append_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _redact(text, secrets):
    for secret in sorted(secrets, key=len, reverse=True):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


def _check(result, secrets, name, expected, actual, predicate=None):
    passed = predicate(actual) if predicate else actual == expected
    result["checks"].append(
        {
            "check": name,
            "expected": _redact(repr(expected), secrets),
            "actual": _redact(repr(actual), secrets),
            "passed": passed,
        }
    )
    if not passed:
        result["failures"].append(
            f"{name}: expected {_redact(repr(expected), secrets)}, "
            f"actual {_redact(repr(actual), secrets)}"
        )


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _load_runtime():
    import agent
    import config
    import generate
    import mcp_client
    import tools
    import trace
    from utils.data_loader import get_example_wardrobe

    return {
        "agent": agent,
        "config": config,
        "generate": generate,
        "mcp_client": mcp_client,
        "tools": tools,
        "trace": trace,
        "get_example_wardrobe": get_example_wardrobe,
    }


def _run_trial(runtime, label, case, secrets, run_label):
    agent = runtime["agent"]
    generate = runtime["generate"]
    mcp_client = runtime["mcp_client"]
    tools = runtime["tools"]
    trace = runtime["trace"]

    prefix = f"{run_label}_" if run_label else ""
    run_log_path = RESULTS / f"{prefix}{label}_runs.jsonl"
    trial_path = RESULTS / f"{prefix}{label}_trials.jsonl"
    prior_run_lines = _read_lines(run_log_path)
    calls_before = generate.call_count()
    stage_calls = {
        "search_listings": 0,
        "suggest_outfit": 0,
        "create_fit_card": 0,
    }
    injection = {}
    stdout = io.StringIO()
    escaped = None
    session = None
    started_at = time.perf_counter()

    original_suggest = agent.suggest_outfit
    original_create = agent.create_fit_card
    original_call_tool = mcp_client.call_tool

    def call_tool(name, arguments):
        if name == "search_listings":
            stage_calls["search_listings"] += 1
        return original_call_tool(name, arguments)

    def injected_exception():
        exception_type = case.get("exception_type", "RuntimeError")
        message = f"Capstone evaluation injected {exception_type}"
        injection.update(type=exception_type, message=message)
        if exception_type == "KeyError":
            raise KeyError(message)
        raise RuntimeError(message)

    def suggest_outfit(item, wardrobe):
        stage_calls["suggest_outfit"] += 1
        if case.get("watch_suggest_item"):
            before = copy.deepcopy(item)
            injection["suggested_item_id"] = item.get("id")
            injection["suggested_item_unchanged"] = None
        if case.get("inject_stage") == "suggest_outfit":
            injected_exception()
        result = original_suggest(item, wardrobe)
        if case.get("watch_suggest_item"):
            injection["suggested_item_unchanged"] = item == before
        return result

    def create_fit_card(outfit, item):
        stage_calls["create_fit_card"] += 1
        if case.get("inject_stage") == "create_fit_card":
            injected_exception()
        return original_create(outfit, item)

    def rate_limit_stub(*args, **kwargs):
        injection.update(
            type="RateLimitExhaustedError",
            message="Capstone evaluation stubbed exhausted rate-limit retries",
        )
        raise generate.RateLimitExhaustedError(injection["message"])

    env_names = ("FITFINDR_LOG", "GEMINI_API_KEY")
    previous_env = {name: os.environ.get(name, UNSET) for name in env_names}
    if case.get("api_key", UNSET) not in (UNSET, None, "") and case["api_key"].strip():
        secrets.add(case["api_key"])

    try:
        os.environ["FITFINDR_LOG"] = str(run_log_path)
        if case.get("api_key", UNSET) is None:
            os.environ.pop("GEMINI_API_KEY", None)
        elif case.get("api_key", UNSET) is not UNSET:
            os.environ["GEMINI_API_KEY"] = case["api_key"]

        trace.start_trace()
        with ExitStack() as stack:
            stack.enter_context(patch.object(generate, "_client", None))
            stack.enter_context(patch.object(agent, "suggest_outfit", suggest_outfit))
            stack.enter_context(patch.object(agent, "create_fit_card", create_fit_card))
            stack.enter_context(patch.object(mcp_client, "call_tool", call_tool))
            if case.get("stub_rate_limit"):
                stack.enter_context(patch.object(tools, "generate", rate_limit_stub))
            with contextlib.redirect_stdout(stdout):
                try:
                    session = agent.run_agent(
                        case["query"], runtime["get_example_wardrobe"]()
                    )
                except Exception as exc:
                    escaped = exc
    finally:
        for name, value in previous_env.items():
            if value is UNSET:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    duration_s = time.perf_counter() - started_at
    calls_after = generate.call_count()
    lines_after = _read_lines(run_log_path)
    appended_lines = lines_after[len(prior_run_lines):]
    record = None
    if len(appended_lines) == 1:
        try:
            record = json.loads(appended_lines[0])
        except json.JSONDecodeError:
            record = None

    session_error = session.get("error") if isinstance(session, dict) else None
    exception_type = (
        type(escaped).__name__
        if escaped is not None
        else (record or {}).get("error_type")
        or injection.get("type")
    )
    exception_message = (
        str(escaped)
        if escaped is not None
        else injection.get("message")
        or (record or {}).get("error_message")
    )
    result = {
        "criterion": label,
        "case": case["name"],
        "query": case["query"],
        "stubbed": bool(case.get("stub_rate_limit") or case.get("inject_stage")),
        "outcome": (record or {}).get("outcome"),
        "exception_type": exception_type,
        "exception_message": _redact(exception_message or "", secrets),
        "session_error": _redact(session_error or "", secrets),
        "_escaped_type": type(escaped).__name__ if escaped is not None else None,
        "duration_s": round(duration_s, 6),
        "output_text": _redact(stdout.getvalue(), secrets),
        "model_calls_observed": calls_after - calls_before,
        "stage_calls": stage_calls,
        "checks": [],
        "failures": [],
    }
    result["_session"] = session
    result["_record"] = record
    result["_appended_lines"] = appended_lines
    result["_injection"] = injection
    return result, trial_path


def _generic_checks(result, secrets):
    _check(
        result,
        secrets,
        "one JSONL run record appended",
        1,
        len(result["_appended_lines"]),
    )
    _check(
        result,
        secrets,
        "no exception escaped run_agent",
        None,
        result.get("_escaped_type"),
    )
    _check(
        result,
        secrets,
        "run log record is a JSON object",
        True,
        isinstance(result["_record"], dict),
    )


def _finalize_trial(result, trial_path):
    record = result.pop("_record")
    session = result.pop("_session")
    appended_lines = result.pop("_appended_lines")
    injection = result.pop("_injection")
    result["passed"] = not result["failures"]
    result["injected_exception"] = injection.get("type")
    _append_json(trial_path, result)
    result["_record"] = record
    result["_session"] = session
    result["_appended_lines"] = appended_lines
    result["_injection"] = injection
    return result


def _c1_checks(result, secrets, expected_outcome="bad_input"):
    record = result["_record"] or {}
    session = result["_session"] or {}
    _generic_checks(result, secrets)
    _check(result, secrets, "outcome", expected_outcome, record.get("outcome"))
    _check(
        result,
        secrets,
        "non-empty session error",
        "non-empty string",
        session.get("error"),
        _is_nonempty_string,
    )
    _check(
        result,
        secrets,
        "search_listings calls",
        0,
        result["stage_calls"]["search_listings"],
    )
    _check(
        result,
        secrets,
        "suggest_outfit calls",
        0,
        result["stage_calls"]["suggest_outfit"],
    )


def _c2_checks(result, secrets, case):
    record = result["_record"] or {}
    session = result["_session"] or {}
    error = session.get("error")
    _generic_checks(result, secrets)
    _check(result, secrets, "failure outcome", case["expected_outcome"], record.get("outcome"))
    _check(result, secrets, "exception type", case["expected_exception"], result["exception_type"])
    _check(
        result,
        secrets,
        "normalized session error",
        "non-empty string without traceback",
        error,
        lambda value: _is_nonempty_string(value) and "Traceback" not in value,
    )
    _check(
        result,
        secrets,
        "no create_fit_card after failure",
        0,
        result["stage_calls"]["create_fit_card"],
    )


def _c3_checks(result, secrets, case):
    record = result["_record"] or {}
    session = result["_session"] or {}
    error = session.get("error") or ""
    _generic_checks(result, secrets)
    _check(result, secrets, "outcome", "unexpected_error", record.get("outcome"))
    _check(result, secrets, "exception type", case["exception_type"], result["exception_type"])
    _check(
        result,
        secrets,
        "session error names failing stage",
        True,
        case["inject_stage"] in error,
    )
    _check(
        result,
        secrets,
        "session error names --trace",
        True,
        "--trace" in error,
    )
    _check(
        result,
        secrets,
        "failing stage called once",
        1,
        result["stage_calls"][case["inject_stage"]],
    )
    if case["inject_stage"] == "suggest_outfit":
        _check(
            result,
            secrets,
            "no later create_fit_card call",
            0,
            result["stage_calls"]["create_fit_card"],
        )


def _c4_checks(result, secrets, case):
    record = result["_record"] or {}
    session = result["_session"] or {}
    _generic_checks(result, secrets)
    _check(result, secrets, "logged outcome", case["expected_outcome"], record.get("outcome"))
    _check(
        result,
        secrets,
        "logged error matches session",
        session.get("error"),
        record.get("error_message"),
    )
    _check(
        result,
        secrets,
        "all 15 run-log fields",
        sorted(LOG_FIELDS),
        sorted(record.keys()) if isinstance(record, dict) else [],
    )
    timings = record.get("stage_durations_s") if isinstance(record, dict) else None
    valid_timings = isinstance(timings, dict) and all(
        isinstance(value, (int, float)) and value >= 0
        for value in timings.values()
    )
    _check(
        result,
        secrets,
        "non-negative stage timings",
        True,
        valid_timings,
    )
    _check(
        result,
        secrets,
        "logged model calls match generator counter delta",
        result["model_calls_observed"],
        record.get("model_calls") if isinstance(record, dict) else None,
    )
    serialized = result["_appended_lines"][0] if result["_appended_lines"] else ""
    leaked_secret = any(secret in serialized for secret in secrets if secret)
    _check(result, secrets, "no secret values in run log", False, leaked_secret)
    if case.get("expected_outcome") == "ok":
        _check(
            result,
            secrets,
            "all three stages called once",
            {"search_listings": 1, "suggest_outfit": 1, "create_fit_card": 1},
            result["stage_calls"],
        )


def _c5_checks(result, secrets):
    record = result["_record"] or {}
    session = result["_session"] or {}
    injection = result["_injection"]
    _generic_checks(result, secrets)
    _check(result, secrets, "outcome", "ok", record.get("outcome"))
    _check(
        result,
        secrets,
        "all three stages called once",
        {"search_listings": 1, "suggest_outfit": 1, "create_fit_card": 1},
        result["stage_calls"],
    )
    selected_id = (session.get("selected_item") or {}).get("id")
    _check(result, secrets, "selected listing ID", "lst_002", selected_id)
    _check(
        result,
        secrets,
        "suggest_outfit receives selected listing ID",
        selected_id,
        injection.get("suggested_item_id"),
    )
    _check(
        result,
        secrets,
        "selected item is unchanged after suggest_outfit",
        True,
        injection.get("suggested_item_unchanged"),
    )
    _check(
        result,
        secrets,
        "non-empty fit card",
        "non-empty string",
        session.get("fit_card"),
        _is_nonempty_string,
    )


def _suite_cases():
    matching = "vintage graphic tee under $30"
    impossible = "neon tuxedo under $2, size XXS"
    return {
        "c1": [
            {"name": "empty", "query": ""},
            {"name": "whitespace", "query": "   "},
            {"name": "price-only", "query": "under $30"},
            {"name": "size-only", "query": "size M"},
        ],
        "c2": [
            {
                "name": "unset-key",
                "query": matching,
                "api_key": None,
                "expected_outcome": "no_key",
                "expected_exception": "MissingAPIKeyError",
            },
            {
                "name": "whitespace-key",
                "query": matching,
                "api_key": "   ",
                "expected_outcome": "no_key",
                "expected_exception": "MissingAPIKeyError",
            },
            {
                "name": "invalid-key",
                "query": matching,
                "api_key": "not-a-real-key",
                "expected_outcome": "model_unavailable",
                "expected_exception": "ModelUnavailable",
            },
            {
                "name": "retry-exhaustion",
                "query": matching,
                "stub_rate_limit": True,
                "expected_outcome": "rate_limited",
                "expected_exception": "RateLimitExhaustedError",
            },
        ],
        "c3": [
            {
                "name": f"{stage}-{exception_type}",
                "query": matching,
                "inject_stage": stage,
                "exception_type": exception_type,
            }
            for stage in ("suggest_outfit", "create_fit_card")
            for exception_type in ("RuntimeError", "KeyError")
        ],
        "c4": [
            {"name": "valid", "query": matching, "expected_outcome": "ok"},
            {
                "name": "bad-input",
                "query": "under $30",
                "expected_outcome": "bad_input",
            },
            {
                "name": "empty-search",
                "query": impossible,
                "expected_outcome": "empty_search",
            },
            {
                "name": "missing-key",
                "query": matching,
                "api_key": "",
                "expected_outcome": "no_key",
            },
            {
                "name": "simulated-stage-exception",
                "query": matching,
                "inject_stage": "suggest_outfit",
                "exception_type": "RuntimeError",
                "expected_outcome": "unexpected_error",
            },
        ],
        "c5": [
            {
                "name": f"matching-query-{number}",
                "query": matching,
                "watch_suggest_item": True,
            }
            for number in range(1, 6)
        ],
    }


def _secrets_from_environment():
    sensitive_names = ("KEY", "TOKEN", "SECRET", "PASSWORD")
    return {
        value
        for name, value in os.environ.items()
        if any(part in name.upper() for part in sensitive_names)
        and value.strip()
        and len(value.strip()) >= 8
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    run_label = parser.parse_args().label
    old_cache = os.environ.get("AI201_CACHE", UNSET)
    os.environ["AI201_CACHE"] = "0"
    try:
        runtime = _load_runtime()
        old_cache_enabled = runtime["config"].CACHE_ENABLED
        runtime["config"].CACHE_ENABLED = False
        secrets = _secrets_from_environment()
        cases_by_criterion = _suite_cases()
        specs = [
            ("c1", "1. Empty/keywordless input", _c1_checks),
            ("c2", "2. API-key/retry containment", _c2_checks),
            ("c3", "3. Unexpected stage exceptions", _c3_checks),
            ("c4", "4. JSONL logging completeness", _c4_checks),
            ("c5", "5. Matching-query consistency", _c5_checks),
        ]
        table_rows = []
        all_trial_results = []

        try:
            for label, target, checker in specs:
                suites = []
                criterion_cases = cases_by_criterion[label]
                for _ in range(3):
                    suite_results = []
                    for case in criterion_cases:
                        case = dict(case)
                        if label == "c5":
                            case["watch_suggest_item"] = True
                        result, trial_path = _run_trial(
                            runtime, label, case, secrets, run_label
                        )
                        if checker in (_c2_checks, _c3_checks, _c4_checks):
                            checker(result, secrets, case)
                        else:
                            checker(result, secrets)
                        finalized = _finalize_trial(result, trial_path)
                        suite_results.append(finalized)
                        all_trial_results.append(finalized)
                    passed = sum(1 for trial in suite_results if trial["passed"])
                    stubbed = any(trial["stubbed"] for trial in suite_results)
                    cell = f"{passed}/{len(suite_results)}"
                    if stubbed:
                        cell += " (stubbed)"
                    suites.append((cell, passed == len(suite_results)))
                verdict = "Pass" if all(ok for _, ok in suites) else "Fail"
                table_rows.append((label, target, suites, verdict))

            total_model_calls = sum(
                trial["model_calls_observed"] for trial in all_trial_results
            )
            print("| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |")
            print("|---|---|---:|---:|---:|---|")
            for label, target, suites, verdict in table_rows:
                print(
                    f"| Criterion {label[1:]} | {target} | {suites[0][0]} | {suites[1][0]} | "
                    f"{suites[2][0]} | {verdict} |"
                )
            print(f"\nModel calls recorded: {total_model_calls}")
        finally:
            runtime["config"].CACHE_ENABLED = old_cache_enabled
    finally:
        if old_cache is UNSET:
            os.environ.pop("AI201_CACHE", None)
        else:
            os.environ["AI201_CACHE"] = old_cache


if __name__ == "__main__":
    main()
