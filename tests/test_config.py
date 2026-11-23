from __future__ import annotations

import pytest
from astrbot_plugin_iona_misc.core.config import PluginConfig


def test_defaults() -> None:
    config = PluginConfig.from_mapping({})
    assert config.sender_block.enabled is True
    assert config.sender_block.sender_ids == ()
    assert config.sender_block.active_ids == ()


@pytest.mark.parametrize("raw", [None, [], "sender_block", {"sender_block": "x"}])
def test_malformed_mapping_falls_back_to_defaults(raw) -> None:
    assert PluginConfig.from_mapping(raw) == PluginConfig()


def test_sender_ids_are_normalized_and_deduplicated() -> None:
    config = PluginConfig.from_mapping(
        {"sender_block": {"sender_ids": [" 10001 ", 10003, "", None, True, "10001"]}}
    )
    assert config.sender_block.sender_ids == ("10001", "10003")


def test_non_list_sender_ids_are_ignored() -> None:
    config = PluginConfig.from_mapping({"sender_block": {"sender_ids": "10001"}})
    assert config.sender_block.sender_ids == ()


def test_disabled_block_keeps_list_but_blocks_nobody() -> None:
    config = PluginConfig.from_mapping(
        {"sender_block": {"enabled": False, "sender_ids": ["10001"]}}
    )
    assert config.sender_block.sender_ids == ("10001",)
    assert config.sender_block.active_ids == ()


def test_non_bool_enabled_uses_default() -> None:
    config = PluginConfig.from_mapping(
        {"sender_block": {"enabled": "false", "sender_ids": ["1"]}}
    )
    assert config.sender_block.enabled is True
