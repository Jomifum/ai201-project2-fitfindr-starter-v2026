"""Append one structured record for each FitFindr agent run."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4


OUTCOMES = {
    "ok",
    "empty_search",
    "bad_input",
    "model_unavailable",
    "mcp_error",
    "no_key",
    "rate_limited",
    "unexpected_error",
}


def write_run(
    query,
    session,
    outcome,
    error_type,
    error_message,
    started_at,
    stage_durations_s,
    start_model_counts,
    model_counts,
) -> None:
    try:
        end_counts = model_counts()
        start_calls, start_tokens, start_cache_hits = start_model_counts
        end_calls, end_tokens, end_cache_hits = end_counts
        selected_item = session.get("selected_item") if session else None
        record = {
            "ts": datetime.now().astimezone().isoformat(),
            "run_id": str(uuid4()),
            "query": query,
            "outcome": outcome if outcome in OUTCOMES else "unexpected_error",
            "error_type": error_type,
            "error_message": error_message,
            "selected_item_id": selected_item.get("id") if selected_item else None,
            "fit_card": session.get("fit_card") if session else None,
            "duration_s": round(time.perf_counter() - started_at, 6),
            "stage_durations_s": {
                name: round(seconds, 6)
                for name, seconds in stage_durations_s.items()
            },
            "model_calls": end_calls - start_calls,
            "prompt_tokens": end_tokens["prompt"] - start_tokens["prompt"],
            "output_tokens": end_tokens["output"] - start_tokens["output"],
            "cache_hits": end_cache_hits - start_cache_hits,
        }
        path = Path(os.environ.get("FITFINDR_LOG") or "logs/runs.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as log_file:
            log_file.write(
                json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str)
                + "\n"
            )
    except Exception as exc:
        warn_write_failure(exc)


def warn_write_failure(exc: Exception) -> None:
    try:
        print(
            f"[run_log] Warning: couldn't write run record ({type(exc).__name__}).",
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        pass
