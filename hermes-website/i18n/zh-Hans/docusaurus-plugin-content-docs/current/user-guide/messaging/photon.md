---
sidebar_position: 18
---

# Photon iMessage

通过 [Photon][photon] 管理服务将 Hermes 连接到 **iMessage**，Photon 负责处理苹果线路分配和滥用防护层，无需你自己运行 Mac 中继。

免费套餐使用 Photon 的共享 iMessage 线路池——不同收件人可能看到不同的发送号码，但每个对话保持稳定。付费商业套餐为每位用户提供相同的专属号码；插件同时支持两者，免费套餐是推荐的起点。

:::info 免费开始使用
Photon 的共享线路池是免费的。无需订阅即可从 Hermes 发送第一条 iMessage——只需一个可以绑定到你账户的手机号。
:::

## 架构

入站消息以**签名 Webhook** 形式到达：Photon 将带有 `X-Spectrum-Signature` 头的 JSON 通过 POST 发送到你注册的 URL，Hermes 的 aiohttp 监听器在将事件分发到 Agent 之前验证 HMAC-SHA256 签名。

出站回复通过一个受监督的小型 **Node sidecar** 进行，该 sidecar 在回环地址上运行 `spectrum-ts` SDK。Photon 目前尚未暴露公共的 HTTP 发送消息端点——这在其路线图中——因此在此之前 sidecar 是调用 `Space.send(...)` 的唯一方式。Python 插件自动启动、监督和关闭 sidecar。当 Photon 推出 HTTP 发送端点后，我们将在后续版本中移除 sidecar。

## 前提条件

- Photon 账户——在 [app.photon.codes][app] 注册
- **Node.js 18.17 或更新版本** 在 PATH 中可用（`node --version`）
- 一个可接收 iMessage 的手机号（用于绑定你的账户）
- 一个可公开访问的 Webhook 接收器 URL——Cloudflare Tunnel、ngrok 或你自己的 Gateway 主机名均可

## 首次设置

运行统一的 Gateway 向导并选择 **Photon iMessage**：

```bash
hermes gateway setup
```

……或直接运行 Photon 设置（向导调用的是同一流程）：

```bash
# 设备码登录 + 项目 + 用户 + sidecar 依赖，一步完成
hermes photon setup --phone +15551234567
```

设置过程：

1. 打开 `https://app.photon.codes/` 进行设备授权
2. 在你的账户下创建 Spectrum 项目
3. 调用 Spectrum 的 `create-user` 端点，使用 `type: shared` 让 Photon 从免费池分配 iMessage 线路
4. 在插件的 sidecar 目录中运行 `npm install`

凭据存储在 `~/.hermes/auth.json` 中的 `credential_pool.photon`（bearer token）和 `credential_pool.photon_project`（项目 ID + 密钥）。

## 授权用户

Photon 使用与所有其他 Hermes 通道相同的授权模型。选择一种方式：

**DM 配对（默认）。** 当未知号码给你的 Photon 线路发送消息时，Hermes 回复一个配对码。通过以下命令批准：

```bash
hermes pairing approve photon <CODE>
```

使用 `hermes pairing list` 查看待处理的配对码和已批准用户。

**预授权特定号码**（在 `~/.hermes/.env` 中）：

```bash
PHOTON_ALLOWED_USERS=+15551234567,+15559876543
```

**开放访问**（仅开发环境，在 `~/.hermes/.env` 中）：

```bash
PHOTON_ALLOW_ALL_USERS=true
```

当设置了 `PHOTON_ALLOWED_USERS` 时，未知发送者会被静默忽略而非提供配对码（白名单信号表明你有意限制了访问）。

### 群聊中需要提及

默认情况下，Hermes 会回复所有已授权的私聊和群聊消息。如需让群聊改为选择加入模式，启用提及门控（私聊始终正常工作）：

```yaml
gateway:
  platforms:
    photon:
      enabled: true
      require_mention: true
```

设置 `require_mention: true` 后，群聊消息除非匹配唤醒词模式，否则被忽略。默认模式匹配 `Hermes` 和 `@Hermes agent` 变体。如需自定义 Agent 名称，设置正则表达式模式：

```yaml
gateway:
  platforms:
    photon:
      require_mention: true
      mention_patterns:
        - '(?<![\w@])@?amos\b[,:\-]?'
```

两个键也接受环境变量（`PHOTON_REQUIRE_MENTION`、`PHOTON_MENTION_PATTERNS`）。这与 BlueBubbles iMessage 通道使用的提及门控模型相同。

## 注册 Webhook

Photon 需要一个可以 POST 的公共 URL。通过 Cloudflare Tunnel 或 ngrok 暴露你的本地监听器（默认端口 8788，路径 `/photon/webhook`），然后：

```bash
hermes photon webhook register https://YOUR-PUBLIC-URL/photon/webhook
```

响应中包含一个 `signingSecret`——**Photon 仅返回一次。** 保存到 `~/.hermes/.env`：

```bash
PHOTON_WEBHOOK_SECRET=v0_64-char-hex...
```

插件验证每个入站 `POST` 请求是否包含此密钥，并拒绝时间戳偏移超过 5 分钟的投递。

## 启动 Gateway

```bash
hermes gateway start --platform photon
```

你会看到类似以下输出：

```
[photon] connected — webhook at 0.0.0.0:8788/photon/webhook, sidecar on 127.0.0.1:8789
```

向你分配的手机号发送一条 iMessage，Hermes 就会回复。

## 状态与故障排查

```bash
hermes photon status
```

输出：

```
Photon iMessage status
──────────────────────
  device token        : ✓ stored
  project id          : 3c90c3cc-0d44-4b50-...
  project key         : ✓ stored
  webhook key         : ✓ set
  node binary         : /usr/bin/node
  sidecar deps        : ✓ installed
```

常见问题：

- **`sidecar deps : ✗ run hermes photon install-sidecar`** — Node 已安装但 `spectrum-ts` 未安装。运行建议的命令。
- **`webhook key : ⚠ unset — verification disabled`** — 插件将接受任何发送到 Webhook URL 的 POST 请求，这是不安全的。重新运行 `hermes photon webhook register` 并保存密钥。
- **`PHOTON_WEBHOOK_PORT` 已被占用** — 通过 `~/.hermes/.env` 设置其他端口。
- **Webhook 可从 localhost 访问但 Photon 无法投递** — Photon 需要公共主机名。Cloudflare Tunnel 是最简单的免费方案。

## Webhook 管理

```bash
hermes photon webhook list                  # 显示已注册的 webhook
hermes photon webhook delete <webhook-id>   # 删除一个
```

## 当前限制

- **入站附件仅含元数据。** 入站 Webhook 包含文件名和 MIME 类型，但没有下载 URL——Photon 将附件检索端点列为路线图项目。
- **出站附件已支持。** Hermes 通过 spectrum-ts 的 `attachment()`/`voice()` 内容构建器经由 sidecar 的 `/send-attachment` 端点发送图片、语音消息、视频和文档。说明文字作为单独的 iMessage 气泡在媒体后发送。
- **Photon 免费配额：** 每台服务器每天 5,000 条消息，每条共享线路每天 50 次新对话启动。如需增加配额，联系 `help@photon.codes`。

## 环境变量

| 变量 | 默认值 | 说明 |
|-----------|--------|------|
| `PHOTON_PROJECT_ID` | 来自 `auth.json` | 由 `hermes photon setup` 设置 |
| `PHOTON_PROJECT_SECRET` | 来自 `auth.json` | 由 `hermes photon setup` 设置 |
| `PHOTON_WEBHOOK_SECRET` | （未设置） | 来自 `hermes photon webhook register` |
| `PHOTON_WEBHOOK_PORT` | `8788` | aiohttp 监听器的本地端口 |
| `PHOTON_WEBHOOK_PATH` | `/photon/webhook` | 监听器挂载的路径 |
| `PHOTON_WEBHOOK_BIND` | `0.0.0.0` | 监听器的绑定地址 |
| `PHOTON_SIDECAR_PORT` | `8789` | sidecar 控制的回环端口 |
| `PHOTON_SIDECAR_AUTOSTART` | `true` | 适配器是否自动启动 sidecar |
| `PHOTON_NODE_BIN` | `which node` | 覆盖 Node 二进制文件路径 |
| `PHOTON_HOME_CHANNEL` | （未设置） | Cron/通知的默认 Space ID |
| `PHOTON_HOME_CHANNEL_NAME` | （未设置） | 主通道的人类可读标签 |
| `PHOTON_ALLOWED_USERS` | （未设置） | 逗号分隔的 E.164 白名单 |
| `PHOTON_ALLOW_ALL_USERS` | `false` | 仅开发环境——接受任何发送者 |
| `PHOTON_REQUIRE_MENTION` | `false` | 在群聊中需要唤醒词才回复 |
| `PHOTON_MENTION_PATTERNS` | Hermes 唤醒词 | 群聊提及的 JSON 列表/逗号/换行正则表达式模式 |
| `PHOTON_API_HOST` | `spectrum.photon.codes` | 覆盖 Spectrum 管理 API 主机 |
| `PHOTON_DASHBOARD_HOST` | `app.photon.codes` | 覆盖 Dashboard/设备登录主机 |

[photon]: https://photon.codes/
[app]: https://app.photon.codes/
