# astrbot_plugin_iona_misc

<div align="center">

[![License: AGPL](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://opensource.org/licenses/agpl-3.0)
![Python Version](https://img.shields.io/badge/Python-%3E%3D3.12%2C%3C4-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.28%2C%3C5-green)

**自用 AstrBot 杂项插件：收纳个人部署里遇到的特殊情况**

</div>

---

## 📖 简介

这个插件不上架插件市场，直接从 GitHub 安装，用来放一些不值得单独成插件的零碎调整。

### 发送者屏蔽

同群里还有别的机器人（比如只发通知的传统 bot）时，AstrBot 会把它的消息当成群友消息处理：
图片逐张调用模型转述、转述内容写进群聊上下文、偶尔触发主动回复，后续每次请求都要带上这些内容。

常见的黑名单插件在消息处理阶段用 `stop_event()` 拦截，但 AstrBot 内置的群聊上下文、
空 @ 等待等处理器优先级是 `sys.maxsize` 一档，总是先于插件执行，所以拦不住。

本插件在**唤醒检查阶段**（流水线第一个阶段）就终止名单内账号的事件，效果是：

| 被跳过的内容 | 说明 |
|---|---|
| 图片转述 | 不再为这些消息调用图片转述模型 |
| 群聊上下文 | 不写入群聊上下文感知和群消息历史 |
| 主动回复 | 不会被抽中主动回复 |
| 所有插件 | 任何插件的监听器、指令都收不到这些消息 |
| 会话限流 | 不计入会话的限流次数，不会因为它刷屏而拖慢真人的消息 |

如果将来 AstrBot 改了流水线、事件没有在唤醒检查阶段结束，插件还会在消息处理阶段以高于所有内置
处理器的优先级再拦一次，并在日志里打一条 warning，列出排在它前面已经执行的处理器。

## 📦 安装

在 AstrBot 管理面板的 插件管理 → 安装 → 从链接安装 中输入：

```text
https://github.com/iona-s/astrbot_plugin_iona_misc
```

更新时在插件列表里点这个插件的更新即可，AstrBot 会重新下载仓库默认分支的源码包。

## ⚙️ 配置说明

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `sender_block.enabled` | `true` | 启用发送者屏蔽；关闭后名单保留但不生效 |
| `sender_block.sender_ids` | 空 | 完全忽略的发送者 ID。QQ（aiocqhttp）填 QQ 号，QQ 官方机器人平台填该用户的 openid |

屏蔽对所有启用了本插件的配置文件生效，不区分会话：

- 配置文件的插件列表是 `*` 时自动包含本插件；手动列出插件的配置文件需要把本插件加进去。
- 屏蔽在唤醒检查阶段完成，WebUI 里按会话关闭本插件不影响屏蔽。

## 🧪 开发

```text
ruff check --config ruff.toml .
ruff format --check --config ruff.toml .
python -m pytest
```

测试说明见 [`tests/README.md`](tests/README.md)。

## 📄 许可证

[AGPL-3.0](LICENSE)
