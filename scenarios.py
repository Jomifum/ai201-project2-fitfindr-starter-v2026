"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Each criterion has a scenario below. Scenario-only wrappers assert the behavior
described by each criterion without changing agent.py.
"""

import re
from unittest.mock import patch

import agent as _agent
import config
import mcp_client as _mcp_client
from generate import ModelUnavailable

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "neon tuxedo under $2, size XXS",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        "name": "selected item reaches outfit tool",
        "query": "graphic tee size L under $30",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "fit card facts and variation",
        "query": "denim jacket under $40, size L",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        "name": "model failure returns session error",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")

_RUN_AGENT = _agent.run_agent
_CRITERION_BY_QUERY = {
    scenario["query"]: scenario["criterion"] for scenario in SCENARIOS
}
_CRITERION_1_TRIALS: list[dict] = []
_CRITERION_4_CARDS: list[str] = []
_CRITERION_4_INPUTS: list[tuple] = []
_CRITERION_4_ATTEMPTS = 0
_CRITERION_4_OUTFIT = "a white tee, straight-leg jeans, and sneakers"


def _check_all(checks: list[tuple], session: dict | None = None) -> None:
    failures = [
        f"{name}: expected {expected!r}; actual={actual!r}"
        for name, passed, expected, actual in checks
        if not passed
    ]
    try:
        assert not failures, "; ".join(failures)
    except AssertionError as exc:
        if session is not None:
            exc.session = session
        raise


def _run_with_criterion_checks(query: str, wardrobe: dict) -> dict:
    criterion = _CRITERION_BY_QUERY.get(query)

    if criterion == 1:
        with patch.object(
            _mcp_client, "call_tool", wraps=_mcp_client.call_tool
        ) as search_call, patch.object(
            _agent, "suggest_outfit", wraps=_agent.suggest_outfit
        ) as outfit_call, patch.object(
            _agent, "create_fit_card", wraps=_agent.create_fit_card
        ) as card_call:
            session = _RUN_AGENT(query, wardrobe)
        results = session.get("search_results") or []
        fit_card = session.get("fit_card")
        _CRITERION_1_TRIALS.append(
            {
                "matching_results": len(results),
                "search_calls": search_call.call_count,
                "outfit_calls": outfit_call.call_count,
                "card_calls": card_call.call_count,
                "fit_card": bool(fit_card),
            }
        )
        if len(_CRITERION_1_TRIALS) == 5:
            passed_count = sum(
                trial["matching_results"] > 0
                and trial["search_calls"] > 0
                and trial["outfit_calls"] > 0
                and trial["card_calls"] > 0
                and trial["fit_card"]
                for trial in _CRITERION_1_TRIALS
            )
            print(
                "Criterion 1 completion check: "
                f"{passed_count}/5 tries (target: at least 4/5)."
            )
            _check_all(
                [
                    (
                        "criterion 1 matching-query completion rate",
                        passed_count >= 4,
                        "at least 4 of 5 tries",
                        {"passed": passed_count, "trials": _CRITERION_1_TRIALS},
                    )
                ],
                session,
            )
        return session

    if criterion == 2:
        with patch.object(
            _agent, "suggest_outfit", wraps=_agent.suggest_outfit
        ) as outfit_call:
            session = _RUN_AGENT(query, wardrobe)
        results = session.get("search_results")
        message = session.get("error") or ""
        names_a_change = any(
            change in message
            for change in ("price ceiling", "different size", "broader keywords")
        )
        _check_all(
            [
                (
                    "criterion 2 impossible query has no listings",
                    results == [],
                    "[]",
                    results,
                ),
                (
                    "criterion 2 stops before suggest_outfit",
                    outfit_call.call_count == 0,
                    0,
                    outfit_call.call_count,
                ),
                (
                    "criterion 2 returns a message naming a change",
                    bool(message) and names_a_change,
                    "non-empty message naming a change",
                    message,
                ),
            ],
            session,
        )
        return session

    if criterion == 3:
        received_items = []
        original_suggest = _agent.suggest_outfit

        def capture_item(new_item, user_wardrobe):
            received_items.append(new_item)
            return original_suggest(new_item, user_wardrobe)

        with patch.object(_agent, "suggest_outfit", side_effect=capture_item):
            session = _RUN_AGENT(query, wardrobe)
        results = session.get("search_results") or []
        selected_id = (session.get("selected_item") or {}).get("id")
        passed_ids = [
            item.get("id") if isinstance(item, dict) else None
            for item in received_items
        ]
        _check_all(
            [
                (
                    "criterion 3 query matches at least one listing",
                    len(results) > 0,
                    "at least 1 listing",
                    len(results),
                ),
                (
                    "criterion 3 suggest_outfit received a new_item",
                    len(received_items) > 0,
                    "at least 1 new_item argument",
                    len(received_items),
                ),
                (
                    "criterion 3 selected id matches ids actually passed",
                    selected_id is not None
                    and bool(passed_ids)
                    and all(item_id == selected_id for item_id in passed_ids),
                    f"all passed ids equal {selected_id!r}",
                    {"selected_id": selected_id, "passed_ids": passed_ids},
                ),
            ],
            session,
        )
        return session

    if criterion == 4:
        global _CRITERION_4_ATTEMPTS
        _CRITERION_4_ATTEMPTS += 1
        received = []
        original_create = _agent.create_fit_card

        def create_fixed_card(outfit, new_item):
            card = original_create(outfit, new_item)
            received.append((outfit, new_item, card))
            return card

        with patch.object(
            _agent, "suggest_outfit", return_value=_CRITERION_4_OUTFIT
        ), patch.object(_agent, "create_fit_card", side_effect=create_fixed_card):
            session = _RUN_AGENT(query, wardrobe)

        card = session.get("fit_card")
        card_text = card if isinstance(card, str) else ""
        _CRITERION_4_CARDS.append(card_text)
        _CRITERION_4_INPUTS.extend(
            (
                item.get("id") if isinstance(item, dict) else None,
                outfit,
            )
            for outfit, item, _ in received
        )

        input_ids = [
            item.get("id") if isinstance(item, dict) else None
            for _, item, _ in received
        ]
        outfits = [outfit for outfit, _, _ in received]
        item = received[-1][1] if received else {}
        sentence_count = len(
            [
                part
                for part in re.split(r"(?<=[.!?])\s+", card_text.strip())
                if part
            ]
        )
        title = item.get("title", "") if isinstance(item, dict) else ""
        price = item.get("price") if isinstance(item, dict) else None
        platform = item.get("platform", "") if isinstance(item, dict) else ""
        price_text = f"${price:g}" if isinstance(price, (int, float)) else str(price)

        checks = [
            (
                "criterion 4 cache is disabled",
                config.CACHE_ENABLED is False,
                False,
                config.CACHE_ENABLED,
            ),
            (
                "criterion 4 temperature is positive",
                config.TEMPERATURE > 0,
                "> 0",
                config.TEMPERATURE,
            ),
            (
                "criterion 4 create_fit_card received the item and outfit",
                len(received) > 0,
                "at least 1 captured create_fit_card call",
                len(received),
            ),
            (
                "criterion 4 captured inputs use the same item and outfit",
                bool(received)
                and all(item_id == input_ids[0] for item_id in input_ids)
                and all(outfit == outfits[0] for outfit in outfits),
                "consistent item id and outfit across captured calls",
                {"item_ids": input_ids, "outfits": outfits},
            ),
            (
                "criterion 4 returned a fit card",
                bool(card_text),
                "non-empty string",
                card,
            ),
            (
                "criterion 4 sentence count",
                2 <= sentence_count <= 4,
                "2 to 4",
                sentence_count,
            ),
            (
                "criterion 4 title occurrence count",
                bool(title) and card_text.count(title) == 1,
                1,
                card_text.count(title) if title else 0,
            ),
            (
                "criterion 4 price occurrence count",
                price is not None and card_text.count(price_text) == 1,
                1,
                card_text.count(price_text),
            ),
            (
                "criterion 4 platform occurrence count",
                bool(platform)
                and card_text.casefold().count(str(platform).casefold()) == 1,
                1,
                card_text.casefold().count(str(platform).casefold()),
            ),
        ]
        if _CRITERION_4_ATTEMPTS == 5:
            distinct_count = len(set(_CRITERION_4_CARDS))
            all_item_ids = [item_id for item_id, _ in _CRITERION_4_INPUTS]
            all_outfits = [outfit for _, outfit in _CRITERION_4_INPUTS]
            checks.extend(
                [
                    (
                        "criterion 4 five generated cards",
                        len(_CRITERION_4_CARDS) == 5
                        and all(_CRITERION_4_CARDS),
                        "5 non-empty cards",
                        {
                            "card_count": len(_CRITERION_4_CARDS),
                            "non_empty_count": sum(bool(value) for value in _CRITERION_4_CARDS),
                        },
                    ),
                    (
                        "criterion 4 same item across five runs",
                        len(all_item_ids) > 0
                        and all(item_id == all_item_ids[0] for item_id in all_item_ids),
                        "one item id across all create_fit_card calls",
                        all_item_ids,
                    ),
                    (
                        "criterion 4 same outfit across five runs",
                        len(all_outfits) > 0
                        and all(outfit == all_outfits[0] for outfit in all_outfits),
                        "one outfit across all create_fit_card calls",
                        all_outfits,
                    ),
                    (
                        "criterion 4 distinct card count across five runs",
                        distinct_count >= 3,
                        "at least 3 distinct strings",
                        {
                            "card_count": len(_CRITERION_4_CARDS),
                            "distinct_count": distinct_count,
                        },
                    ),
                ]
            )
            print(
                "Criterion 4 variation check: "
                f"{distinct_count} distinct strings across "
                f"{len(_CRITERION_4_CARDS)} tries (target: at least 3 across 5)."
            )
        _check_all(checks, session)
        return session

    if criterion == 5:
        with patch.object(
            _agent,
            "suggest_outfit",
            side_effect=ModelUnavailable("scenario test"),
        ) as outfit_call:
            session = _RUN_AGENT(query, wardrobe)
        message = session.get("error")
        _check_all(
            [
                (
                    "criterion 5 injected ModelUnavailable",
                    outfit_call.call_count > 0,
                    "suggest_outfit called and raised ModelUnavailable",
                    outfit_call.call_count,
                ),
                (
                    "criterion 5 returns a non-empty error session",
                    bool(message),
                    "non-empty session.error",
                    message,
                ),
            ],
            session,
        )
        return session

    return _RUN_AGENT(query, wardrobe)


_agent.run_agent = _run_with_criterion_checks


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
