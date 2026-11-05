import io
import unittest
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from PIL import Image

from player_images import (
    FALLBACK_JERSEY_PATH,
    _fetch_player_photo,
    photo_url,
    player_image,
    player_photo_urls,
)


def image_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, format="PNG")
    return buffer.getvalue()


def response(data, content_type="image/png"):
    result = io.BytesIO(data)
    result.headers = Message()
    result.headers["Content-Type"] = content_type
    return result


class PlayerImagesTests(unittest.TestCase):
    def test_current_source_uses_stable_code(self):
        self.assertEqual(
            photo_url({"code": 154561, "photo": "outdated.jpg"}),
            "https://resources.premierleague.com/premierleague25/photos/players/110x140/154561.png",
        )

    def test_older_snapshot_can_use_photo_filename(self):
        self.assertEqual(
            player_photo_urls({"photo": "154561.jpg"}),
            player_photo_urls({"code": 154561}),
        )

    def test_missing_or_temporary_code_uses_black_shirt_without_fetch(self):
        with patch("player_images._fetch_player_photo") as fetch:
            for player in ({}, {"photo": ""}, {"photo": "invalid.jpg"},
                           {"code": 0}, {"code": 123, "has_temporary_code": True}):
                with self.subTest(player=player):
                    self.assertIsNone(photo_url(player))
                    self.assertEqual(player_image(player), str(FALLBACK_JERSEY_PATH))
            fetch.assert_not_called()
        self.assertTrue(FALLBACK_JERSEY_PATH.is_file())

    def test_valid_current_photo_does_not_fetch_legacy(self):
        data = image_bytes()
        with patch("player_images.urllib.request.urlopen", return_value=response(data)) as fetch:
            self.assertEqual(_fetch_player_photo.__wrapped__(("current", "legacy")), data)
            self.assertEqual(fetch.call_count, 1)

    def test_legacy_photo_used_when_current_unavailable(self):
        data = image_bytes()
        error = HTTPError("current", 403, "Forbidden", {}, None)
        with patch("player_images.urllib.request.urlopen", side_effect=[error, response(data)]) as fetch:
            self.assertEqual(_fetch_player_photo.__wrapped__(("current", "legacy")), data)
            self.assertEqual(fetch.call_args_list[1].args[0], "legacy")

    def test_network_failure_returns_black_shirt(self):
        _fetch_player_photo.clear()
        with patch("player_images.urllib.request.urlopen", side_effect=URLError("offline")):
            self.assertEqual(player_image({"code": 987654321}), str(FALLBACK_JERSEY_PATH))
        _fetch_player_photo.clear()

    def test_error_html_or_invalid_image_cannot_reach_streamlit_image(self):
        for data, content_type in [(b"<html>Error</html>", "text/html"),
                                   (b"not a real image", "image/png")]:
            with self.subTest(content_type=content_type):
                with patch("player_images.urllib.request.urlopen", return_value=response(data, content_type)):
                    self.assertIsNone(_fetch_player_photo.__wrapped__(("current",)))

    def test_image_is_cached_across_reruns(self):
        _fetch_player_photo.clear()
        data = image_bytes()
        with patch("player_images.urllib.request.urlopen", return_value=response(data)) as fetch:
            self.assertEqual(player_image({"code": 123456789}), data)
            self.assertEqual(player_image({"code": 123456789}), data)
            self.assertEqual(fetch.call_count, 1)
        _fetch_player_photo.clear()


if __name__ == "__main__":
    unittest.main()
