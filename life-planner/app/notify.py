"""Push notifications via ntfy (https://ntfy.sh). Install the ntfy app and subscribe to your topic."""

import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)


def send(title: str, message: str, priority: str = "default", tags: str | None = None) -> bool:
    if not settings.ntfy_topic:
        log.info("ntfy not configured; would send: %s - %s", title, message)
        return False
    headers = {"Title": title, "Priority": priority}
    if tags:
        headers["Tags"] = tags
    try:
        response = httpx.post(
            f"{settings.ntfy_url}/{settings.ntfy_topic}", content=message.encode(), headers=headers, timeout=10
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        log.exception("Failed to send ntfy notification")
        return False
