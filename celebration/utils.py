from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple
from urllib.parse import quote_plus, urlencode

from django.utils.text import slugify

from .models import Guest, RSVP

DICEBEAR_BASE = "https://api.dicebear.com/9.x"
SKIN_PALETTE = {
    "porcelain": "eeb4a4",
    "rosy": "e7a391",
    "sienna": "d78774",
    "amber": "b16a5b",
    "espresso": "92594b",
}

HAIR_COLORS = {
    "midnight": "362c47",
    "espresso": "3b2315",
    "chestnut": "6c4545",
    "copper": "b45b3e",
    "honey": "f29c65",
    "platinum": "dee1f5",
    "rose-quartz": "e16381",
}

HAIR_STYLES = {
    "short": "shortCombover",
    "long": "extraLong",
}

BACKGROUND_SWATCHES = {
    "champagne": "f7e8d8",
    "lavender": "b19acb",
    "midnight": "1c1c3c",
    "sage": "b8c4ae",
    "rose": "f3c0c6",
}

ACCENT_EYES = {
    "na": "open",
    "floral": "happy",
    "pocket-square": "wink",
    "veil": "sleep",
    "bow-tie": "glasses",
}

ACCENT_MOUTH = {
    "bow-tie": "smirk",
}

SEATS_PER_ROW = 6
ROW_SPACING = 3.5
ROW_OFFSET = 2
SEAT_SPACING = 2.4
AISLE_HALF_WIDTH = 2.5
AISLE_GAP = 0.5
AVATAR_DEPTH_OFFSET = 1.2
SEATS_PER_SIDE = math.ceil(SEATS_PER_ROW / 2)
SIDE_CENTER_OFFSET = AISLE_HALF_WIDTH + AISLE_GAP + ((SEATS_PER_SIDE - 1) * SEAT_SPACING) / 2


def compute_seat_position(row_index: int, seat_index: int) -> Dict[str, float]:
    """
    Translate logical row/seat indexes into the same coordinate space used by the Three.js scene.
    """
    if seat_index < SEATS_PER_SIDE:
        side = -1
        index_within_side = seat_index
    else:
        side = 1
        index_within_side = seat_index - SEATS_PER_SIDE
    lateral = (index_within_side - (SEATS_PER_SIDE - 1) / 2) * SEAT_SPACING
    x = side * SIDE_CENTER_OFFSET + lateral
    z = -((row_index + ROW_OFFSET) * ROW_SPACING) - AVATAR_DEPTH_OFFSET
    return {"x": x, "z": z}


def find_or_create_guest(full_name: str, email: str | None) -> Tuple[Guest, bool]:
    normalized_name = full_name.strip()
    if email:
        normalized_email = email.strip().lower()
    else:
        normalized_email = f"{slugify(normalized_name) or 'guest'}-{Guest.objects.count()+1}@uploads.local"
    guest = Guest.objects.filter(
        full_name__iexact=normalized_name,
        email__iexact=normalized_email,
    ).first()
    if guest:
        return guest, True

    guest = Guest.objects.create(
        full_name=normalized_name,
        email=normalized_email,
        invited=False,
        verified=False,
    )
    return guest, False


def avatar_url(avatar_config: Dict[str, str], fallback_seed: str) -> str:
    """
    Convert the stored configuration to a DiceBear personas API URL.
    """
    skin = SKIN_PALETTE.get(avatar_config.get("skin"), SKIN_PALETTE["porcelain"])
    hair_color = HAIR_COLORS.get(avatar_config.get("hair"), HAIR_COLORS["espresso"])
    hair_style = HAIR_STYLES.get(avatar_config.get("hairStyle"), HAIR_STYLES["short"])
    background = BACKGROUND_SWATCHES.get(
        avatar_config.get("outfit"), BACKGROUND_SWATCHES["lavender"]
    )
    accent = avatar_config.get("accent") or "na"
    params = {
        "seed": quote_plus(avatar_config.get("signature") or fallback_seed or "guest"),
        "skinColor[]": skin,
        "hair[]": hair_style,
        "hairColor[]": hair_color,
        "backgroundColor[]": background,
        "eyes[]": ACCENT_EYES.get(accent, ACCENT_EYES["na"]),
        "mouth[]": ACCENT_MOUTH.get(accent, "smile"),
        "nose[]": "mediumRound",
        "size": "210",
    }
    query = urlencode(params, doseq=True)
    return f"{DICEBEAR_BASE}/personas/svg?{query}"


def build_seating_chart(responses: Iterable[RSVP], seats_per_row: int = SEATS_PER_ROW) -> List[dict]:
    row_names = ["A", "B", "C", "D", "E", "F"]
    seating_plan: List[dict] = []

    seat_idx = 0
    for response in responses:
        # Get avatar configs - handle both list and dict formats for backward compatibility
        if isinstance(response.avatar_config, list):
            avatar_configs = response.avatar_config
        elif isinstance(response.avatar_config, dict):
            avatar_configs = [response.avatar_config]
        else:
            # Default config if none exists
            avatar_configs = [{
                "skin": "porcelain",
                "hair": "espresso",
                "hairStyle": "short",
                "outfit": "lavender",
                "accent": "floral",
                "signature": response.guest.full_name.strip() or "guest-avatar",
            }]
        
        # Create one seat per avatar in the party
        for avatar_idx, avatar_config in enumerate(avatar_configs):
            row_index = seat_idx // seats_per_row
            row_label = row_names[row_index] if row_index < len(row_names) else f"R{row_index+1}"
            seat_number = (seat_idx % seats_per_row) + 1
            seat_index = seat_idx % seats_per_row
            position = compute_seat_position(row_index, seat_index)
            
            # Build name - if multiple people, add a suffix
            if len(avatar_configs) > 1:
                name = f"{response.guest.full_name} ({avatar_idx + 1})"
            else:
                name = response.guest.full_name
            
            seating_plan.append(
                {
                    "row": row_label,
                    "seat_number": seat_number,
                    "name": name,
                    "config": avatar_config,  # Pass the config object, not the URL
                    "row_index": row_index,
                    "seat_index": seat_index,
                    "position": position,
                }
            )
            seat_idx += 1

    return seating_plan
