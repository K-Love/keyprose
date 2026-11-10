"""
Listing Writer AI Module
========================
Generates professional MLS listing descriptions from property details.

Prompt template example:
    "Write a {tone} real estate listing description for a {beds}-bedroom,
     {baths}-bathroom home at {address}. The home is {sqft} sq ft, built in
     {year_built}, and features: {features}. Target length: {length}."

Fallback: deterministic template-based generator (no API key needed).
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any, Dict
from services.ai_client import generate_text


# ─── Tone descriptors ─────────────────────────────────────────────────────────

_TONE_OPENERS = {
    "luxury": [
        "Welcome to an extraordinary residence where sophistication meets comfort.",
        "Indulge in the pinnacle of refined living at this exceptional estate.",
        "Presenting a rare opportunity to own a truly magnificent home.",
    ],
    "family": [
        "Welcome home! This warm and inviting property is perfect for growing families.",
        "Create lasting memories in this charming family-friendly retreat.",
        "Everything your family needs — space, comfort, and a neighborhood you'll love.",
    ],
    "investment": [
        "Exceptional investment opportunity in a high-demand rental corridor.",
        "Strong cap rate potential with this turnkey income-producing property.",
        "Add this cash-flowing asset to your real estate portfolio today.",
    ],
    "casual": [
        "Okay, this one's a gem — and it won't last long!",
        "Love where you live! This adorable home checks every box.",
        "Seriously, you need to see this place in person.",
    ],
    "professional": [
        "This well-appointed property offers an exceptional combination of location and value.",
        "Presenting a meticulously maintained residence in a sought-after neighborhood.",
        "A rare opportunity to acquire a move-in ready home with premium finishes throughout.",
    ],
}

_LENGTH_TARGETS = {
    "short": 100,
    "medium": 200,
    "long": 350,
}


def _deterministic_listing(details: Dict[str, Any], tone: str, length: str) -> str:
    """Generate a listing description without an AI API."""
    import hashlib

    tone = tone.lower() if tone.lower() in _TONE_OPENERS else "professional"
    openers = _TONE_OPENERS[tone]
    h = int(hashlib.md5(str(details).encode()).hexdigest(), 16)
    opener = openers[h % len(openers)]

    beds = _or_default(details.get("beds"), 3)
    baths = _or_default(details.get("baths"), 2)
    sqft = _or_default(details.get("sqft"), 1800)
    address = _clean_text(details.get("address"))
    year_built = details.get("year_built") or ""
    price = details.get("price") or ""
    neighborhood = _clean_text(details.get("neighborhood"))
    features = _clean_features(details.get("features"))

    feature_str = ""
    if features:
        if len(features) == 1:
            feature_str = features[0]
        elif len(features) == 2:
            feature_str = f"{features[0]} and {features[1]}"
        else:
            feature_str = ", ".join(features[:-1]) + f", and {features[-1]}"

    year_str = f"Built in {year_built}, this " if year_built else "This "
    place = f" at {address}" if address else ""
    nbhd_str = f" in the desirable {neighborhood} area" if neighborhood else ""
    price_str = f" Listed at ${price:,}." if price else ""

    short = (
        f"{opener} {year_str}{beds}-bedroom, {baths}-bathroom home{place}{nbhd_str} "
        f"offers {sqft:,} sq ft of thoughtfully designed living space.{price_str}"
    )

    if length == "short":
        return short

    medium_extra = ""
    if feature_str:
        medium_extra = (
            f" Highlights include {feature_str}. "
            "The open-concept layout flows seamlessly from the gourmet kitchen "
            "to the inviting living area, perfect for both everyday living and entertaining. "
            "The primary suite is a true retreat, complete with a spa-inspired bath and generous closet space."
        )
    else:
        medium_extra = (
            " The open-concept layout flows seamlessly from the gourmet kitchen "
            "to the inviting living area, perfect for both everyday living and entertaining. "
            "The primary suite is a true retreat, complete with a spa-inspired bath and generous closet space."
        )

    medium = short + medium_extra

    if length == "medium":
        return medium

    long_extra = (
        " Step outside to a beautifully landscaped backyard — ideal for summer gatherings "
        "or quiet evenings under the stars. Additional highlights include updated systems, "
        "ample storage throughout, and an attached garage. "
        "Conveniently located near top-rated schools, premier dining, boutique shopping, "
        "and major commuter routes. "
        "Homes like this don't stay on the market long — schedule your private tour today "
        "and experience everything this exceptional property has to offer!"
    )

    return medium + long_extra


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _or_default(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    return value


def _clean_features(value: Any) -> list:
    if not isinstance(value, list):
        return []
    cleaned = []
    for feature in value:
        if isinstance(feature, str):
            feature = feature.strip()
        if feature:
            cleaned.append(feature)
    return cleaned


def _neighborhood_text(value: Any) -> str:
    return _clean_text(value)


def listing_prompt(details: Dict[str, Any], tone: str = "professional", length: str = "medium") -> str:
    """Prompt sent to the model. Neighborhood is included only when the user provided one."""
    target_words = _LENGTH_TARGETS.get(length, 200)
    features_str = ", ".join(details.get("features", [])) or "modern finishes"
    address = details.get("address", "a prime location")
    neighborhood = _neighborhood_text(details.get("neighborhood"))
    place = f"{address} in the {neighborhood} neighborhood" if neighborhood else address
    year_clause = f", built in {details.get('year_built')}" if details.get("year_built") else ""

    return (
        f"Write a {tone} real estate listing description for a "
        f"{details.get('beds', 3)}-bedroom, {details.get('baths', 2)}-bathroom home "
        f"at {place}. "
        f"The home is {details.get('sqft', 1800):,} sq ft"
        f"{year_clause}. "
        f"Key features: {features_str}. "
        f"Price: ${details.get('price', 0):,}. "
        f"Target approximately {target_words} words. "
        "Do not include the price in the listing text. "
        "Write in second person (you/your). End with a call to action."
    )


def generate_listing(details: Dict[str, Any], tone: str = "professional", length: str = "medium") -> str:
    """
    Generate a real estate listing description.

    Args:
        details: Property details dict (address, beds, baths, sqft, features, etc.)
        tone: Writing tone — luxury | family | investment | casual | professional
        length: Output length — short | medium | long

    Returns:
        Listing description string.
    """
    import os

    if not os.getenv("OPENAI_API_KEY"):
        return _deterministic_listing(details, tone, length)

    prompt = listing_prompt(details, tone, length)

    system = (
        "You are an expert real estate copywriter who crafts compelling, "
        "accurate MLS listing descriptions that attract qualified buyers."
    )

    return generate_text(prompt, max_tokens=600, system_message=system)
