"""Official FPL player portraits with a local shirt fallback."""

import io
import ssl
import urllib.request
from pathlib import Path

import certifi
import streamlit as st
from PIL import Image


PHOTO_BASE_URL = "https://resources.premierleague.com/premierleague25/photos/players/110x140"
LEGACY_PHOTO_BASE_URL = "https://resources.premierleague.com/premierleague/photos/players/110x140"
FALLBACK_JERSEY_PATH = Path(__file__).resolve().parent / "assets" / "jersey_pl.png"


def player_photo_urls(player):
    """Use the same stable player code and current CDN as the official FPL app."""
    if player.get("has_temporary_code"):
        return ()

    code = str(player.get("code") or "").strip()
    if not code.isdecimal() or int(code) <= 0:
        # Older/offline bootstrap snapshots may only include the photo filename.
        code = str(player.get("photo") or "").strip().split(".")[0].removeprefix("p")
    if not code.isdecimal() or int(code) <= 0:
        return ()

    return (
        f"{PHOTO_BASE_URL}/{code}.png",
        f"{LEGACY_PHOTO_BASE_URL}/p{code}.png",
    )


def photo_url(player, *, legacy=False):
    urls = player_photo_urls(player)
    return urls[1 if legacy else 0] if urls else None


@st.cache_data(ttl=3600, max_entries=1024, show_spinner=False)
def _fetch_player_photo(urls):
    context = ssl.create_default_context(cafile=certifi.where())
    for url in urls:
        try:
            with urllib.request.urlopen(url, context=context, timeout=5) as response:
                if not response.headers.get_content_type().startswith("image/"):
                    continue
                data = response.read()
            # A successful HTTP response can still contain an invalid image.
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            return data
        except (OSError, ValueError, SyntaxError):
            continue
    return None


def player_image(player):
    """Return verified image bytes or the same black shirt used on the squad pitch."""
    urls = player_photo_urls(player)
    return (_fetch_player_photo(urls) if urls else None) or str(FALLBACK_JERSEY_PATH)
