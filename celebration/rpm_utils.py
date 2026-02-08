"""
Ready Player Me integration utilities for Django
"""
import os
import requests
from typing import Optional, Dict

# Set this in your Django settings or environment variables
READY_PLAYER_ME_APPLICATION_ID = os.environ.get("READY_PLAYER_ME_APPLICATION_ID", "")

READY_PLAYER_ME_API_BASE = "https://api.readyplayer.me/v1"


def create_anonymous_rpm_user() -> Optional[Dict[str, str]]:
    """
    Create an anonymous Ready Player Me user.
    Returns: { "user_id": str, "token": str } or None if failed
    """
    if not READY_PLAYER_ME_APPLICATION_ID:
        print("Warning: READY_PLAYER_ME_APPLICATION_ID not set in environment")
        return None
    
    try:
        response = requests.post(
            f"{READY_PLAYER_ME_API_BASE}/users",
            json={
                "data": {
                    "applicationId": READY_PLAYER_ME_APPLICATION_ID,
                }
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "user_id": data["data"]["id"],
            "token": data["data"]["token"],
        }
    except Exception as e:
        print(f"Error creating Ready Player Me user: {e}")
        return None


def get_avatar_gltf_url(user_id: str, token: str) -> Optional[str]:
    """
    Get the GLTF model URL for a Ready Player Me user's avatar.
    """
    try:
        response = requests.get(
            f"{READY_PLAYER_ME_API_BASE}/avatars",
            params={"userId": user_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        data = response.json()
        # The response structure may vary - adjust based on actual API response
        if isinstance(data, dict) and "data" in data:
            avatars = data["data"]
            if isinstance(avatars, list) and len(avatars) > 0:
                return avatars[0].get("modelUrl") or avatars[0].get("gltfUrl")
            elif isinstance(avatars, dict):
                return avatars.get("modelUrl") or avatars.get("gltfUrl")
        return None
    except Exception as e:
        print(f"Error getting Ready Player Me avatar URL: {e}")
        return None
