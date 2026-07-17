"""
Tracking Service for Email Opens and Link Clicks.

Provides:
- Injects 1x1 transparent tracking pixel tag into HTML body
- Replaces regular <a> href links with tracking redirect endpoints
- Generates transparent 1x1 GIF bytes for tracking pixel response
"""
import base64
import re
import urllib.parse
from typing import Tuple

# Standard 1x1 transparent GIF image bytes
TRANSPARENT_GIF_BYTES = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


class TrackingService:
    """Service for modifying email HTML body to inject tracking elements."""

    @staticmethod
    def get_pixel_gif() -> bytes:
        """Return 1x1 transparent GIF bytes for HTTP response."""
        return TRANSPARENT_GIF_BYTES

    @staticmethod
    def inject_tracking(
        body_html: str,
        recipient_id: str,
        campaign_id: str,
        base_url: str = "http://localhost",
    ) -> Tuple[str, str]:
        """
        Inject open tracking pixel and wrap href links for click tracking.

        Returns:
            (tracking_token, tracked_html_body)
        """
        if not body_html:
            body_html = ""

        token = f"{campaign_id}_{recipient_id}"

        # 1. Open tracking pixel URL
        pixel_url = f"{base_url.rstrip('/')}/api/v1/tracking/open/{token}.png"
        pixel_tag = f'<img src="{pixel_url}" width="1" height="1" style="display:none !important;" alt="" />'

        # 2. Click tracking link replacement
        def replace_link(match: re.Match) -> str:
            original_url = match.group(1)
            # Skip tracking links, mailto:, #, or unsubscribes
            if (
                not original_url
                or original_url.startswith("#")
                or original_url.startswith("mailto:")
                or "/tracking/" in original_url
            ):
                return match.group(0)

            encoded = urllib.parse.quote(original_url, safe="")
            click_url = f"{base_url.rstrip('/')}/api/v1/tracking/click/{token}?target={encoded}"
            return f'href="{click_url}"'

        tracked_body = re.sub(r'href=["\'](https?://[^"\']+)["\']', replace_link, body_html)

        # 3. Append pixel before </body> or at the end
        if "</body>" in tracked_body:
            tracked_body = tracked_body.replace("</body>", f"{pixel_tag}</body>")
        else:
            tracked_body = f"{tracked_body}{pixel_tag}"

        return token, tracked_body
