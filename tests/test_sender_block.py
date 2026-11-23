from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from astrbot.core.star.star_handler import star_handlers_registry
from astrbot_plugin_iona_misc.core import plugin as plugin_module
from astrbot_plugin_iona_misc.core.plugin import IonaMiscPlugin
from astrbot_plugin_iona_misc.core.sender_block import (
    BLOCKLIST,
    PRIORITY,
    BlockedSenderFilter,
    handlers_ahead,
)

BOT_ID = "10001"
UMO = "test:GroupMessage:20000"


class FakeEvent:
    def __init__(self, sender_id: object, activated: list[str] | None = None) -> None:
        self.sender_id = sender_id
        self.unified_msg_origin = UMO
        self.stopped = False
        self.extras = {
            "activated_handlers": [
                SimpleNamespace(handler_full_name=name) for name in activated or []
            ]
        }

    def get_sender_id(self) -> object:
        return self.sender_id

    def stop_event(self) -> None:
        self.stopped = True

    def get_extra(self, key: str, default=None):
        return self.extras.get(key, default)


class RecordingLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, message: str, *args) -> None:
        self.warnings.append(message % args)

    def info(self, *_args) -> None:
        pass


@pytest.fixture()
def plugin():
    instance = IonaMiscPlugin(
        SimpleNamespace(), {"sender_block": {"sender_ids": [BOT_ID]}}
    )
    yield instance
    BLOCKLIST.clear()


def test_filter_stops_blocked_sender(plugin) -> None:
    event = FakeEvent(BOT_ID)
    assert BlockedSenderFilter().filter(event, {}) is True
    assert event.stopped


@pytest.mark.parametrize("sender_id", ["10002", "", None])
def test_filter_ignores_other_senders(plugin, sender_id) -> None:
    event = FakeEvent(sender_id)
    assert BlockedSenderFilter().filter(event, {}) is False
    assert not event.stopped


def test_filter_matches_integer_sender_ids(plugin) -> None:
    event = FakeEvent(int(BOT_ID))
    assert BlockedSenderFilter().filter(event, {}) is True


@pytest.mark.asyncio
async def test_terminate_clears_blocklist(plugin) -> None:
    await plugin.terminate()
    assert BlockedSenderFilter().filter(FakeEvent(BOT_ID), {}) is False


def test_disabled_config_blocks_nobody() -> None:
    IonaMiscPlugin(
        SimpleNamespace(),
        {"sender_block": {"enabled": False, "sender_ids": [BOT_ID]}},
    )
    assert BlockedSenderFilter().filter(FakeEvent(BOT_ID), {}) is False


def test_handler_registered_above_every_builtin_priority() -> None:
    (handler,) = [
        item
        for item in star_handlers_registry
        if item.handler_name == "ignore_blocked_sender"
    ]
    assert sys.maxsize < PRIORITY
    assert handler.extras_configs["priority"] == PRIORITY
    assert any(isinstance(item, BlockedSenderFilter) for item in handler.event_filters)


@pytest.mark.asyncio
async def test_fallback_handler_stops_and_warns_once(plugin, monkeypatch) -> None:
    recorder = RecordingLogger()
    monkeypatch.setattr(plugin_module, "logger", recorder)
    own = f"{IonaMiscPlugin.__module__}_ignore_blocked_sender"
    event = FakeEvent(BOT_ID, ["builtin_handle_session", own, "other_on_message"])

    await plugin.ignore_blocked_sender(event)
    await plugin.ignore_blocked_sender(FakeEvent(BOT_ID))

    assert event.stopped
    assert len(recorder.warnings) == 1
    assert "builtin_handle_session" in recorder.warnings[0]
    assert "other_on_message" not in recorder.warnings[0]


def test_handlers_ahead_without_own_entry_lists_everything() -> None:
    event = FakeEvent(BOT_ID, ["a", "b"])
    assert handlers_ahead(event, "missing") == ["a", "b"]
    assert handlers_ahead(FakeEvent(BOT_ID), "missing") == []
