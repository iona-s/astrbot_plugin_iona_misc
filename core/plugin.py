"""AstrBot registration and lifecycle coordination."""

from __future__ import annotations

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.star.star import star_map
from astrbot.core.star.star_handler import star_handlers_registry

from .config import PluginConfig
from .sender_block import BLOCKLIST, PRIORITY, BlockedSenderFilter, handlers_ahead

_IMPLEMENTATION_MODULE = __name__


class IonaMiscPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        self.config = PluginConfig.from_mapping(config or {})
        BLOCKLIST.configure(self.config.sender_block.active_ids)
        self._fallback_warned = False

    async def initialize(self) -> None:
        blocked = self.config.sender_block.active_ids
        if blocked:
            logger.info("Ignoring all messages from %d sender(s)", len(blocked))

    async def terminate(self) -> None:
        BLOCKLIST.clear()

    @filter.custom_filter(BlockedSenderFilter, priority=PRIORITY)
    async def ignore_blocked_sender(self, event: AstrMessageEvent) -> None:
        """忽略屏蔽名单中发送者的消息"""
        # BlockedSenderFilter normally ends the pipeline during the wake-up
        # check, so reaching this handler means AstrBot kept running later
        # stages. Stop here as well and say so once.
        event.stop_event()
        if self._fallback_warned:
            return
        self._fallback_warned = True
        own_name = f"{type(self).__module__}_{self.ignore_blocked_sender.__name__}"
        ahead = handlers_ahead(event, own_name)
        logger.warning(
            "Blocked sender %s reached the handler stage: this AstrBot version "
            "no longer ends the pipeline at the wake-up check, so the whitelist, "
            "rate limit and preprocessing stages ran. Handlers that ran first: %s",
            event.get_sender_id(),
            ", ".join(ahead) or "none",
        )


def bind_loader_module(loader_module: str) -> None:
    """Bind registrations from this implementation module to AstrBot's loader module."""
    if loader_module in star_map:
        return
    metadata = star_map.pop(_IMPLEMENTATION_MODULE, None)
    if metadata is None:
        raise RuntimeError("iona misc plugin metadata was not registered")
    metadata.module_path = loader_module
    star_map[loader_module] = metadata
    IonaMiscPlugin.__module__ = loader_module

    for handler in list(star_handlers_registry):
        if handler.handler_module_path != _IMPLEMENTATION_MODULE:
            continue
        old_full_name = handler.handler_full_name
        handler.handler.__module__ = loader_module
        handler.handler_module_path = loader_module
        handler.handler_full_name = f"{loader_module}_{handler.handler_name}"
        star_handlers_registry.star_handlers_map.pop(old_full_name, None)
        star_handlers_registry.star_handlers_map[handler.handler_full_name] = handler
