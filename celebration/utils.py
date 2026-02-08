from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple
from urllib.parse import quote_plus, urlencode

from django.utils.text import slugify

from .models import Guest, RSVP

DICEBEAR_BASE = "https://api.dicebear.com/9.x"
SKIN_PALETTE = {
    "dark1": "614335",
    "medium1": "ae5d29",
    "light1": "edb98a",
    # Additional skin tones from before
    "porcelain": "eeb4a4",
    "rosy": "e7a391",
    "sienna": "d78774",
    "amber": "b16a5b",
    "espresso": "92594b",
}

HAIR_COLORS = {
    "dark1": "2c1b18",
    "dark2": "4a312c",
    "brown1": "724133",
    "brown2": "a55728",
    "brown3": "b58143",
    "red": "c93305",
    "blonde1": "d6b370",
    "blonde2": "e8e1e1",
}

HAIR_STYLES = {
    "shortWaved": "shortWaved",
    "longButNotTooLong": "longButNotTooLong",
    "straightAndStrand": "straightAndStrand",
    "sides": "sides",
    "shortFlat": "shortFlat",
    "curvy": "curvy",
}

BACKGROUND_SWATCHES = {
    "champagne": "f7e8d8",
    "lavender": "b19acb",
    "midnight": "1c1c3c",
    "sage": "b8c4ae",
    "rose": "f3c0c6",
}

ACCENT_EYES = {
    "na": "default",
    "floral": "happy",
    "pocket-square": "wink",
    "veil": "sleep",
    "bow-tie": "default",  # Glasses will be handled via accessories
}

ACCENT_MOUTH = {
    "na": "default",
    "floral": "smile",
    "pocket-square": "smile",
    "veil": "default",
    "bow-tie": "smirk",
}

CLOTHING_STYLES = {
    "blazer": "blazerAndShirt",
    "vneck": "shirtVNeck",
}

ACCESSORIES_OPTIONS = {
    "none": "blank",
    "glasses": "prescription02",
}

ACCESSORIES_COLORS = {
    "dark": "3c4f5c",
    "blue": "65c9ff",
    "black": "262e33",
}

CLOTHES_COLORS = {
    "pink": "ff488e",
    "blue": "65c9ff",
    "purple": "b19acb",  # Using lavender as purple
    "green": "a7ffc4",
    "red": "ff5c5c",
    "black": "262e33",
}

# Legacy mapping for accent-based accessories (for backward compatibility)
FACIAL_HAIR_OPTIONS = {
    "none": "blank",
    "beard": "beardLight",
    "mustache": "moustacheMagnum",
}

ACCENT_ACCESSORIES = {
    "na": "blank",
    "floral": "blank",
    "pocket-square": "blank",
    "veil": "blank",
    "bow-tie": "prescription01",  # Glasses for bow-tie accent
}

# Simple layout: all rows have 2 pews (5 seats each) = 10 seats per row
SEATS_PER_PEW = 5
SEATS_PER_ROW = SEATS_PER_PEW * 2  # 10 seats per row

ROW_SPACING = 6.5
ROW_OFFSET = 0.5
SEAT_SPACING = 2.4
AISLE_HALF_WIDTH = 2.5
AISLE_GAP = 0.5
AVATAR_DEPTH_OFFSET = 1.2

# All rows: 2 pews, 5 seats each
SIDE_CENTER_OFFSET = AISLE_HALF_WIDTH + AISLE_GAP + ((SEATS_PER_PEW - 1) * SEAT_SPACING) / 2


def compute_seat_position(row_index: int, seat_index: int) -> Dict[str, float]:
    """
    Translate logical row/seat indexes into the same coordinate space used by the Three.js scene.
    All rows: [Left Pew 5] [Aisle] [Right Pew 5] = 10 seats per row
    """
    z = -((row_index + ROW_OFFSET) * ROW_SPACING) - AVATAR_DEPTH_OFFSET
    
    # All rows: 2 pews, 5 seats each
    if seat_index < SEATS_PER_PEW:
        side = -1
        index_within_side = seat_index
    else:
        side = 1
        index_within_side = seat_index - SEATS_PER_PEW
    lateral = (index_within_side - (SEATS_PER_PEW - 1) / 2) * SEAT_SPACING
    x = side * SIDE_CENTER_OFFSET + lateral
    
    return {"x": x, "z": z}


def find_or_create_guest(full_name: str, email: str | None) -> Tuple[Guest, bool]:
    normalized_name = full_name.strip()
    
    # If email is provided, search by both name and email
    if email:
        normalized_email = email.strip().lower()
        guest = Guest.objects.filter(
            full_name__iexact=normalized_name,
            email__iexact=normalized_email,
        ).first()
        if guest:
            return guest, True
        # Create with provided email
        guest = Guest.objects.create(
            full_name=normalized_name,
            email=normalized_email,
            invited=False,
            verified=False,
        )
        return guest, False
    else:
        # If no email, search by name only
        guest = Guest.objects.filter(full_name__iexact=normalized_name).first()
        if guest:
            return guest, True
        # Create with placeholder email
        normalized_email = f"{slugify(normalized_name) or 'guest'}-{Guest.objects.count()+1}@uploads.local"
        guest = Guest.objects.create(
            full_name=normalized_name,
            email=normalized_email,
            invited=False,
            verified=False,
        )
        return guest, False


def avatar_url(avatar_config: Dict[str, str], fallback_seed: str) -> str:
    """
    Convert the stored configuration to a DiceBear avataaars API URL.
    """
    skin = SKIN_PALETTE.get(avatar_config.get("skin"), SKIN_PALETTE["light1"])
    hair_color = HAIR_COLORS.get(avatar_config.get("hair"), HAIR_COLORS["dark1"])
    hair_style = HAIR_STYLES.get(avatar_config.get("hairStyle"), HAIR_STYLES["shortFlat"])
    clothes_color = CLOTHES_COLORS.get(avatar_config.get("clothesColor"), CLOTHES_COLORS["blue"])
    
    # Facial hair: use facialHair field or default to none
    facial_hair = FACIAL_HAIR_OPTIONS.get(
        avatar_config.get("facialHair"), "none"
    )
    
    # Accessories: use accessories field or default to blank
    accessories = ACCESSORIES_OPTIONS.get(
        avatar_config.get("accessories"), "none"
    )
    
    params = {
        "seed": quote_plus(avatar_config.get("signature") or fallback_seed or "guest"),
        "skinColor": skin,
        "hairColor": hair_color,
        "top": hair_style,
        "clothing": avatar_config.get("clothesType", "collarAndSweater"),  # Use selected clothing style
        "clothesColor": clothes_color,
        "eyes": "default",  # Default eyes
        "eyebrows": "defaultNatural",
        "mouth": "smile",  # Default smile
        "facialHairColor": hair_color,  # Facial hair and eyebrow color matches hair color
    }
    
    # Only add facial hair if not "none", otherwise set probability to 0
    if facial_hair == "blank":
        params["facialHairProbability"] = "0"
    else:
        params["facialHair"] = facial_hair
        params["facialHairProbability"] = "100"  # Ensure facial hair appears when selected
    
    # Only add accessories if not "none", otherwise set probability to 0
    if accessories == "blank":
        params["accessoriesProbability"] = "0"
    else:
        params["accessories"] = accessories
        params["accessoriesProbability"] = "100"  # Ensure accessories appear when selected
    
    query = urlencode(params, doseq=True)
    return f"{DICEBEAR_BASE}/avataaars/svg?{query}"


def build_seating_chart(responses: Iterable[RSVP], seats_per_row: int = None) -> List[dict]:
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
            # Calculate which row this seat belongs to
            # All rows have 10 seats per row
            row_index = seat_idx // SEATS_PER_ROW
            seat_index = seat_idx % SEATS_PER_ROW
            
            row_label = row_names[row_index] if row_index < len(row_names) else f"R{row_index+1}"
            seat_number = seat_index + 1
            position = compute_seat_position(row_index, seat_index)
            
            # Build name - if multiple people, add a suffix
            if len(avatar_configs) > 1:
                name = f"{response.guest.full_name} ({avatar_idx + 1})"
            else:
                name = response.guest.full_name
            
            # Build avatar URL from config
            avatar_url_str = avatar_url(avatar_config, name)
            
            seating_plan.append(
                {
                    "row": row_label,
                    "seat_number": seat_number,
                    "name": name,
                    "config": avatar_config,  # Keep config for backup/3D
                    "avatar_url": avatar_url_str,  # Add 2D avatar URL
                    "row_index": row_index,
                    "seat_index": seat_index,
                    "position": position,
                }
            )
            seat_idx += 1

    return seating_plan
