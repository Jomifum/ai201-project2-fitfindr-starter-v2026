"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Keep testing them independently so failures
stay easy to isolate.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

The **Tool Inventory** section of the README records their inputs, outputs,
and empty cases. Keep those contracts aligned with these implementations.
"""

import json
import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     Match case-insensitively by whole alphanumeric token, so
                     "M" matches "S/M" but "L" does not match "XL".
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    query_terms = set(re.findall(r"[a-z]+|\d+", description.casefold()))
    if not query_terms:
        return []

    requested_size = set(re.findall(r"[a-z]+|\d+", (size or "").casefold()))
    matches = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue

        listing_size = set(re.findall(r"[a-z]+|\d+", listing["size"].casefold()))
        if requested_size and not requested_size.issubset(listing_size):
            continue

        searchable_text = " ".join(
            str(listing.get(field) or "")
            for field in ("title", "description", "category", "style_tags", "brand")
        )
        if score := len(query_terms & set(re.findall(r"[a-z]+|\d+", searchable_text.casefold()))):
            matches.append((score, listing))

    matches.sort(key=lambda match: -match[0])
    return [listing for _, listing in matches[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    wardrobe_items = wardrobe.get("items", [])
    has_wardrobe_items = bool(wardrobe_items)
    wardrobe_guidance = (
        "Use only the listed wardrobe pieces and name the pieces you use."
        if has_wardrobe_items
        else "The wardrobe is empty. Give general styling advice using hypothetical basics, and do not imply the user owns them."
    )
    prompt = (
        "Suggest one or two wearable outfits centered on this secondhand item. "
        "Be specific about colors, layers, and occasion when useful.\n\n"
        f"{wardrobe_guidance}\n\n"
        "Item and wardrobe data:\n"
        + json.dumps(
            {"new_item": new_item, "wardrobe_items": wardrobe_items},
            ensure_ascii=False,
            indent=2,
        )
    )
    if response := generate(
        prompt,
        system="You are a practical personal stylist. Give concise, specific outfit suggestions grounded in the supplied data.",
    ).strip():
        return response

    title = new_item.get("title", "This item")
    if has_wardrobe_items:
        first_piece = wardrobe_items[0].get("name", "a piece from your wardrobe")
        return f"Try styling {title} with {first_piece}."
    return f"Try styling {title} with a neutral base layer and comfortable shoes."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    title = new_item.get("title", "A thrifted find")
    price = new_item.get("price", "unknown")
    price_text = f"${price:g}" if isinstance(price, (int, float)) else str(price)
    platform = new_item.get("platform", "a resale platform")
    style_tags = new_item.get("style_tags", [])
    vibe = ", ".join(style_tags[:2]) if style_tags else "easygoing"

    if not outfit or not outfit.strip():
        return (
            f"{title} is listed for {price_text} on {platform}; "
            f"its {vibe} vibe makes it a distinctive thrifted find."
        )

    prompt = (
        "Write a post-ready fit-card caption in 2–4 sentences. Mention the "
        "listing title, price, and platform exactly once each. Describe a "
        "specific vibe, use the outfit suggestion, and do not invent listing "
        "facts. Return only the caption.\n\n"
        f"Listing title: {title}\n"
        f"Price: {price_text}\n"
        f"Platform: {platform}\n"
        f"Style tags: {', '.join(style_tags)}\n"
        f"Outfit suggestion: {outfit}"
    )
    if response := generate(
        prompt,
        system="You write concise, natural secondhand fashion captions. Follow the requested sentence count and include each required listing detail exactly once.",
    ).strip():
        return response
    return (
        f"{title} is listed for {price_text} on {platform}; "
        f"its {vibe} vibe makes it a distinctive thrifted find."
    )
