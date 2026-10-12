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
_CRITERION_4_CARDS: list[str] = []
_CRITERION_4_ITEM_ID = None
_CRITERION_4_OUTFIT = "a white tee, straight-leg jeans, and sneakers"


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
        assert search_call.call_count == 1, (
            f"search_listings MCP call count expected 1, got {search_call.call_count}; "
            f"session.error={session.get('error')!r}; "
            f"session.fit_card={session.get('fit_card')!r}"
        )
        assert outfit_call.call_count == 1, (
            f"suggest_outfit call count expected 1, got {outfit_call.call_count}; "
            f"session.error={session.get('error')!r}; "
            f"session.fit_card={session.get('fit_card')!r}"
        )
        assert card_call.call_count == 1, (
            f"create_fit_card call count expected 1, got {card_call.call_count}; "
            f"session.error={session.get('error')!r}; "
            f"session.fit_card={session.get('fit_card')!r}"
        )
        assert bool(session["fit_card"]), (
            f"fit_card truthiness expected True, got {bool(session['fit_card'])}; "
            f"session.error={session.get('error')!r}; "
            f"session.fit_card={session.get('fit_card')!r}"
        )
        return session

    if criterion == 2:
        with patch.object(
            _agent, "suggest_outfit", wraps=_agent.suggest_outfit
        ) as outfit_call:
            session = _RUN_AGENT(query, wardrobe)
        message = session.get("error") or ""
        assert outfit_call.call_count == 0 and session["fit_card"] is None
        assert any(
            change in message
            for change in ("price ceiling", "different size", "broader keywords")
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
        assert len(received_items) == 1
        assert session["selected_item"]["id"] == received_items[0]["id"]
        return session

    if criterion == 4:
        global _CRITERION_4_ITEM_ID
        assert config.CACHE_ENABLED is False and config.TEMPERATURE > 0
        received = []
        original_create = _agent.create_fit_card

        def create_fixed_card(outfit, new_item):
            received.append((outfit, new_item))
            return original_create(outfit, new_item)

        with patch.object(
            _agent, "suggest_outfit", return_value=_CRITERION_4_OUTFIT
        ), patch.object(_agent, "create_fit_card", side_effect=create_fixed_card):
            session = _RUN_AGENT(query, wardrobe)

        assert len(received) == 1 and session["fit_card"]
        outfit, item = received[0]
        item_id = item["id"]
        if _CRITERION_4_ITEM_ID is None:
            _CRITERION_4_ITEM_ID = item_id
        assert item_id == _CRITERION_4_ITEM_ID and outfit == _CRITERION_4_OUTFIT

        card = session["fit_card"]
        sentence_count = len(
            [part for part in re.split(r"(?<=[.!?])\s+", card.strip()) if part]
        )
        assert 2 <= sentence_count <= 4
        assert card.count(item["title"]) == 1
        assert card.count(f"${item['price']:g}") == 1
        assert card.casefold().count(item["platform"].casefold()) == 1

        _CRITERION_4_CARDS.append(card)
        if len(_CRITERION_4_CARDS) == 5:
            print(
                "Criterion 4 variation check: "
                f"{len(set(_CRITERION_4_CARDS))} distinct strings across 5 tries "
                "(target: at least 3)."
            )
        return session

    if criterion == 5:
        with patch.object(
            _agent,
            "suggest_outfit",
            side_effect=ModelUnavailable("scenario test"),
        ):
            session = _RUN_AGENT(query, wardrobe)
        assert session.get("search_results") and session.get("error")
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
