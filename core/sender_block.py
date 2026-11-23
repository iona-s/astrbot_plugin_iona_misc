"""Drop every event from blocked senders before AstrBot processes it."""

from __future__ import annotations

import sys
from collections.abc import Iterable

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.config import AstrBotConfig

# AstrBot's built-in handlers sit as high as sys.maxsize (4.28 session control
# agent) or sys.maxsize - 1 / - 2 (4.29 empty-mention and group context). Equal
# priorities keep registration order, where built-ins win, so go one above.
# Python ints are unbounded and AstrBot only uses the value as a sort key.
PRIORITY = sys.maxsize + 1


class SenderBlocklist:
    """Sender IDs whose events AstrBot should ignore entirely."""

    def __init__(self) -> None:
        self._ids: frozenset[str] = frozenset()

    def configure(self, sender_ids: Iterable[str]) -> None:
        self._ids = frozenset(sender_ids)

    def clear(self) -> None:
        self._ids = frozenset()

    def blocks(self, sender_id: object) -> bool:
        return str(sender_id) in self._ids


# The filter instance is created when the handler is registered, before the
# plugin is instantiated, so the plugin configures this shared blocklist.
BLOCKLIST = SenderBlocklist()


class BlockedSenderFilter(filter.CustomFilter):
    """Stop events from blocked senders during AstrBot's wake-up check.

    AstrBot evaluates handler filters in WakingCheckStage, the first pipeline
    stage, and ends the pipeline after any stage that stops the event. Stopping
    here skips the whitelist, rate limit, preprocessing and every handler, so
    blocked messages are never captioned, recorded, answered or counted against
    the session rate limit. Returning True activates the fallback handler in
    case a future AstrBot release keeps running later stages.
    """

    def filter(self, event: AstrMessageEvent, cfg: AstrBotConfig) -> bool:
        sender_id = event.get_sender_id()
        if not BLOCKLIST.blocks(sender_id):
            return False
        event.stop_event()
        logger.debug(
            "Ignored message from blocked sender %s in %s",
            sender_id,
            event.unified_msg_origin,
        )
        return True


def handlers_ahead(event: AstrMessageEvent, full_name: str) -> list[str]:
    """Return the handlers AstrBot activated before the handler ``full_name``."""
    activated = event.get_extra("activated_handlers", None) or []
    names = [getattr(item, "handler_full_name", "?") for item in activated]
    return names[: names.index(full_name)] if full_name in names else names
