"""Load the plugin next to AstrBot's built-in star and drive the wake-up check.

Run in a clean process (see ``test_pipeline.py``) or directly against any AstrBot
install with ``python -m tests.astrbot_pipeline_smoke`` from the plugin root.
"""

from __future__ import annotations

import copy
import inspect
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import astrbot
import astrbot.core.star.star_manager as star_manager_module
from astrbot.core.config.default import DEFAULT_CONFIG
from astrbot.core.message.components import Image, Plain
from astrbot.core.pipeline.waking_check.stage import WakingCheckStage
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.platform.astrbot_message import AstrBotMessage, Group, MessageMember
from astrbot.core.platform.message_type import MessageType
from astrbot.core.platform.platform_metadata import PlatformMetadata
from astrbot.core.star.session_plugin_manager import SessionPluginManager
from astrbot.core.star.star_handler import EventType, star_handlers_registry
from astrbot.core.star.star_manager import PluginManager

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
PLUGIN_NAME = PLUGIN_ROOT.name
MODULE_PATH = f"data.plugins.{PLUGIN_NAME}.main"
OWN_HANDLER = f"{MODULE_PATH}_ignore_blocked_sender"
BUILTIN_MODULE = "astrbot.builtin_stars.astrbot.main"
BUILTIN_GROUP_CONTEXT = f"{BUILTIN_MODULE}_on_message"

SELF_ID = "10000"
BLOCKED_ID = "10001"
MEMBER_ID = "10002"
GROUP_ID = "20000"


class _FakeContext:
    def get_all_stars(self):
        return star_manager_module.star_registry

    def get_registered_star(self, name):
        return next(
            (item for item in star_manager_module.star_registry if item.name == name),
            None,
        )

    def get_config(self, umo=None):
        return {}


class _NoopRecorder:
    def schedule(self, _event) -> None:
        return None


async def _global_get(_key, default=None):
    return default


async def _sync_configs():
    return None


async def _all_handlers(_event, handlers):
    return handlers


def _event(sender_id: str) -> AstrMessageEvent:
    message = AstrBotMessage()
    message.type = MessageType.GROUP_MESSAGE
    message.self_id = SELF_ID
    message.session_id = GROUP_ID
    message.message_id = "1"
    message.group = Group(group_id=GROUP_ID)
    message.sender = MessageMember(user_id=sender_id, nickname="sender")
    message.message = [
        Plain("明日方舟 活动预告"),
        Image(file="https://example.com/a.png"),
    ]
    message.message_str = "明日方舟 活动预告"
    message.raw_message = None
    platform = PlatformMetadata(name="aiocqhttp", description="test", id="test")
    return AstrMessageEvent(message.message_str, message, platform, GROUP_ID)


async def _wake_check(stage: WakingCheckStage, event: AstrMessageEvent) -> list[str]:
    result = stage.process(event)
    if inspect.isasyncgen(result):
        async for _ in result:
            break
    elif inspect.isawaitable(result):
        await result
    activated = event.get_extra("activated_handlers", None) or []
    return [handler.handler_full_name for handler in activated]


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def _exercise_wake_check() -> None:
    message_handlers = [
        handler.handler_full_name
        for handler in star_handlers_registry.get_handlers_by_event_type(
            EventType.AdapterMessageEvent
        )
    ]
    _check(
        message_handlers[:1] == [OWN_HANDLER],
        f"plugin handler is not first: {message_handlers[:4]}",
    )
    _check(
        BUILTIN_GROUP_CONTEXT in message_handlers,
        f"built-in group context handler missing: {message_handlers}",
    )

    config = copy.deepcopy(DEFAULT_CONFIG)
    config["wake_prefix"] = ["/"]
    config["admins_id"] = []
    stage = WakingCheckStage()
    await stage.initialize(
        SimpleNamespace(astrbot_config=config, db_helper=None, astrbot_config_id="x")
    )
    stage._umo_auto_name_recorder = _NoopRecorder()
    SessionPluginManager.filter_handlers_by_session = staticmethod(_all_handlers)

    blocked = _event(BLOCKED_ID)
    activated = await _wake_check(stage, blocked)
    _check(blocked.is_stopped(), "blocked sender was not stopped at the wake check")
    _check(activated[:1] == [OWN_HANDLER], f"unexpected activation: {activated}")

    member = _event(MEMBER_ID)
    activated = await _wake_check(stage, member)
    _check(not member.is_stopped(), "regular member was stopped at the wake check")
    _check(OWN_HANDLER not in activated, f"plugin handler activated: {activated}")
    _check(
        BUILTIN_GROUP_CONTEXT in activated,
        f"built-in group context no longer activates for members: {activated}",
    )


async def run() -> None:
    isolated_root = TESTS_ROOT / "pipeline-work"
    shutil.rmtree(isolated_root, ignore_errors=True)
    isolated_root.mkdir()
    try:
        plugin_store = isolated_root / "data" / "plugins"
        plugin_store.mkdir(parents=True)
        shutil.copytree(
            PLUGIN_ROOT,
            plugin_store / PLUGIN_NAME,
            ignore=shutil.ignore_patterns(
                ".git", ".pytest_cache", ".ruff_cache", "__pycache__", "tests"
            ),
        )
        config_dir = isolated_root / "data" / "config"
        config_dir.mkdir()
        (config_dir / f"{PLUGIN_NAME}_config.json").write_text(
            json.dumps({"sender_block": {"enabled": True, "sender_ids": [BLOCKED_ID]}}),
            encoding="utf-8",
        )

        star_manager_module.sp.global_get = _global_get
        star_manager_module.sync_command_configs = _sync_configs
        manager = PluginManager(_FakeContext(), {})
        manager.plugin_store_path = str(plugin_store)
        manager.plugin_config_path = str(config_dir)
        manager.reserved_plugin_path = str(
            Path(astrbot.__file__).parent / "builtin_stars"
        )
        sys.path.insert(0, str(isolated_root))
        try:
            for dir_name in ("astrbot", PLUGIN_NAME):
                success, error = await manager.load(specified_dir_name=dir_name)
                if not success:
                    raise RuntimeError(f"loading {dir_name} failed: {error}")
            await _exercise_wake_check()
            for module_path in (MODULE_PATH, BUILTIN_MODULE):
                await manager._terminate_plugin(
                    star_manager_module.star_map[module_path]
                )
        finally:
            if str(isolated_root) in sys.path:
                sys.path.remove(str(isolated_root))
            star_manager_module.star_handlers_registry.clear()
            star_manager_module.star_map.clear()
            star_manager_module.star_registry.clear()
    finally:
        shutil.rmtree(isolated_root, ignore_errors=True)
    print("pipeline smoke passed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
