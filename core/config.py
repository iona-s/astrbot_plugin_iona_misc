"""Configuration normalization."""

from __future__ import annotations

from dataclasses import dataclass, field

from astrbot.api import logger


def _mapping(value: object) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _bool(raw: dict, section: str, key: str, default: bool) -> bool:
    value = raw.get(key, default)
    if isinstance(value, bool):
        return value
    logger.warning("Invalid %s.%s (%s); using default %s", section, key, value, default)
    return default


def _ids(raw: dict, section: str, key: str) -> tuple[str, ...]:
    value = raw.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        logger.warning("Invalid %s.%s (%s); expected a list", section, key, value)
        return ()
    ids: dict[str, None] = {}
    for item in value:
        if isinstance(item, bool) or not isinstance(item, str | int):
            logger.warning("Ignored invalid %s.%s entry %r", section, key, item)
            continue
        if text := str(item).strip():
            ids[text] = None
    return tuple(ids)


@dataclass(frozen=True)
class SenderBlockConfig:
    enabled: bool = True
    sender_ids: tuple[str, ...] = ()

    @property
    def active_ids(self) -> tuple[str, ...]:
        return self.sender_ids if self.enabled else ()


@dataclass(frozen=True)
class PluginConfig:
    sender_block: SenderBlockConfig = field(default_factory=SenderBlockConfig)

    @classmethod
    def from_mapping(cls, raw: object) -> PluginConfig:
        section = _mapping(_mapping(raw).get("sender_block"))
        return cls(
            sender_block=SenderBlockConfig(
                enabled=_bool(section, "sender_block", "enabled", True),
                sender_ids=_ids(section, "sender_block", "sender_ids"),
            )
        )
