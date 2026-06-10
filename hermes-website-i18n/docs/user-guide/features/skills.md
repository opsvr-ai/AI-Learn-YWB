---
sidebar_position: 2
title: "Skills 系统"
description: "按需知识文档 — 渐进式披露、智能体管理的 skills 以及 Skills Hub"
---

# Skills 系统

Skills 是智能体可以在需要时加载的按需知识文档。它们遵循**渐进式披露**模式以最小化 token 消耗，并与 [agentskills.io](https://agentskills.io/specification) 开放标准兼容。

所有 skills 存放在 **`~/.hermes/skills/`** — 这是主目录和数据源。在全新安装时，内置 skills 从代码仓库复制过来。通过 Hub 安装和智能体创建的 skills 也都存储在此处。智能体可以修改或删除任何 skill。

你也可以将 Hermes 指向**外部 skill 目录** — 与本地目录一起扫描的额外文件夹。请参阅下方的[外部 Skill 目录](#外部-skill-目录)。

另请参阅：

- [内置 Skills 目录](/docs/reference/skills-catalog)
- [官方可选 Skills 目录](/docs/reference/optional-skills-catalog)

## 使用 Skills

每个已安装的 skill 都会自动作为斜杠命令可用：

```bash
# 在 CLI 或任何消息平台中：
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor
/plan design a rollout for migrating our auth provider

# 仅输入 skill 名称即可加载它，并让智能体询问你需要什么：
/excalidraw
```

内置的 `plan` skill 是一个很好的示例。运行 `/plan [请求]` 会加载该 skill 的指令，告诉 Hermes 在需要时检查上下文，编写 markdown 实施计划而非直接执行任务，并将结果保存到活动工作区/后端工作目录下的 `.hermes/plans/` 中。

你还可以通过自然对话与 skills 交互：

```bash
hermes chat --toolsets skills -q "What skills do you have?"
hermes chat --toolsets skills -q "Show me the axolotl skill"
```

## 渐进式披露

Skills 使用 token 高效的加载模式：

```
Level 0: skills_list()           → [{name, description, category}, ...]   (~3k tokens)
Level 1: skill_view(name)        → 完整内容 + 元数据       (视具体内容而定)
Level 2: skill_view(name, path)  → 指定的引用文件       (视具体内容而定)
```

智能体仅在实际需要时才加载完整的 skill 内容。

## SKILL.md 格式

```markdown
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
platforms: [macos, linux]     # 可选 — 限制为特定操作系统平台
metadata:
  hermes:
    tags: [python, automation]
    category: devops
    fallback_for_toolsets: [web]    # 可选 — 条件激活（见下文）
    requires_toolsets: [terminal]   # 可选 — 条件激活（见下文）
    config:                          # 可选 — config.yaml 设置
      - key: my.setting
        description: "What this controls"
        default: "value"
        prompt: "Prompt for setup"
---

# Skill 标题

## 何时使用
此 skill 的触发条件。

## 操作步骤
1. 第一步
2. 第二步

## 常见陷阱
- 已知的失败模式及修复方法

## 验证方法
如何确认操作已成功。
```

### 平台特定 Skills

Skills 可以使用 `platforms` 字段限制自身适用的操作系统：

| 值 | 匹配 |
|-------|---------|
| `macos` | macOS (Darwin) |
| `linux` | Linux |
| `windows` | Windows |

```yaml
platforms: [macos]            # 仅 macOS（例如 iMessage、Apple 提醒事项、FindMy）
platforms: [macos, linux]     # macOS 和 Linux
```

设置后，在不兼容的平台上，该 skill 会自动从系统提示、`skills_list()` 和斜杠命令中隐藏。如果省略，该 skill 将在所有平台上加载。

## Skill 输出与媒体投递

当 skill 响应（或任何智能体响应）中包含媒体文件的裸绝对路径时 — 例如 `/home/user/screenshots/diagram.png` — 网关会自动检测该路径，将其从可见文本中剥离，并以原生方式将文件投递给用户的聊天（Telegram 照片、Discord 附件等），而不是在消息中保留原始路径。

对于音频文件，`[[audio_as_voice]]` 指令会将音频文件升级为支持平台（Telegram、WhatsApp）上的原生语音消息气泡。

### 强制文档式投递：`[[as_document]]`

有时你需要**相反的效果**，即不希望内联预览：你希望文件作为可下载的附件投递，而不是重新压缩的图片气泡。典型例子是高分辨率截图或图表 — Telegram 的 `sendPhoto` 会将其重新压缩到约 200 KB、1280 px，严重影响可读性。一张 1-2 MB 的 PNG 通过 `sendDocument` 发送则能保留原始字节。

如果响应（或其中的任何文本 — 通常是最后一行）包含字面指令 `[[as_document]]`，则该响应中提取的每个媒体路径都将以文档/文件附件而不是图片气泡的方式投递：

```
Here is your rendered chart:

/home/user/.hermes/cache/chart-q4-2025.png

[[as_document]]
```

该指令会在投递前被剥离，用户永远不会看到它。粒度有意设计为按响应的全有或全无：发出一次 `[[as_document]]`，同一响应中的所有图片路径都会以文档形式投递。这与 `[[audio_as_voice]]` 的作用域一致。

在以下场景中从 skill 使用它：

- 你生成的截图或图表需要作为文件使用（用于在其他工具中编辑、归档、完整分享）。
- 默认的有损预览会模糊细节（小文字、像素级精确的图表、颜色敏感的渲染）。

没有独立文档路径的平台（例如 SMS）会回退到它们拥有的任何附件机制。

### 条件激活（回退 Skills）

Skills 可以根据当前会话中可用的工具自动显示或隐藏自身。这对于**回退 skills** 最有用 — 即仅在高级工具不可用时才出现的免费或本地替代方案。

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # 仅当这些 toolsets 不可用时才显示
    requires_toolsets: [terminal]     # 仅当这些 toolsets 可用时才显示
    fallback_for_tools: [web_search]  # 仅当这些特定工具不可用时才显示
    requires_tools: [terminal]        # 仅当这些特定工具可用时才显示
```

| 字段 | 行为 |
|-------|----------|
| `fallback_for_toolsets` | 当所列 toolsets 可用时，skill **隐藏**。当它们缺失时显示。 |
| `fallback_for_tools` | 同上，但检查单个工具而不是 toolsets。 |
| `requires_toolsets` | 当所列 toolsets 不可用时，skill **隐藏**。当它们存在时显示。 |
| `requires_tools` | 同上，但检查单个工具。 |

**示例：** 内置的 `duckduckgo-search` skill 使用了 `fallback_for_toolsets: [web]`。当设置了 `FIRECRAWL_API_KEY` 时，web toolset 可用，智能体使用 `web_search` — DuckDuckGo skill 保持隐藏。如果 API 密钥缺失，web toolset 不可用，DuckDuckGo skill 自动出现作为回退。

没有任何条件字段的 skills 行为与之前完全一样 — 它们始终显示。

## 加载时安全设置

Skills 可以声明所需的环境变量而不会从发现列表中消失：

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

当检测到缺失的值时，Hermes 仅在本地 CLI 中实际加载 skill 时才安全地询问该值。你可以跳过设置并继续使用该 skill。消息界面从不在聊天中索要密钥 — 它们会告诉你改用 `hermes setup` 或 `~/.hermes/.env` 在本地设置。

设置后，声明的环境变量会**自动传递**到 `execute_code` 和 `terminal` 沙箱 — skill 的脚本可以直接使用 `$TENOR_API_KEY`。对于非 skill 的环境变量，请使用 `terminal.env_passthrough` 配置选项。详情请参阅[环境变量透传](/docs/user-guide/security#环境变量透传)。

### Skill 配置设置

Skills 也可以声明非机密的配置设置（路径、偏好），存储在 `config.yaml` 中：

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
```

设置存储在 config.yaml 中的 `skills.config` 下。`hermes config migrate` 会提示未配置的设置，`hermes config show` 会显示它们。当 skill 加载时，其已解析的配置值会被注入到上下文中，使智能体自动了解已配置的值。

详情请参阅 [Skill 设置](/docs/user-guide/configuration#skill-设置) 和 [创建 Skills — 配置设置](/docs/developer-guide/creating-skills#配置设置-configyaml)。

## Skill 目录结构

```text
~/.hermes/skills/                  # 单一数据源
├── mlops/                         # 分类目录
│   ├── axolotl/
│   │   ├── SKILL.md               # 主要指令（必需）
│   │   ├── references/            # 附加文档
│   │   ├── templates/             # 输出格式
│   │   ├── scripts/               # 可从 skill 调用的辅助脚本
│   │   └── assets/                # 补充文件
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/                # 智能体创建的 skill
│       ├── SKILL.md
│       └── references/
├── .hub/                          # Skills Hub 状态
│   ├── lock.json
│   ├── quarantine/
│   └── audit.log
└── .bundled_manifest              # 跟踪已植入的内置 skills
```

## 外部 Skill 目录

如果你在 Hermes 之外维护 skills — 例如，由多个 AI 工具共享的 `~/.agents/skills/` 目录 — 你可以让 Hermes 也扫描这些目录。

在 `~/.hermes/config.yaml` 中的 `skills` 部分添加 `external_dirs`：

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - /home/shared/team-skills
    - ${SKILLS_REPO}/skills
```

路径支持 `~` 展开和 `${VAR}` 环境变量替换。

### 工作原理

- **本地创建，原地更新**：新智能体创建的 skills 写入 `~/.hermes/skills/`。现有 skills 在找到它们的位置进行修改，包括 `external_dirs` 下的 skills，当智能体使用 `skill_manage` 操作（如 `patch`、`edit`、`write_file`、`remove_file` 或 `delete`）时。
- **外部目录不是写保护边界**：如果外部 skill 目录对 Hermes 进程可写，智能体管理的 skill 更新可以更改该目录中的文件。如果共享的外部 skills 必须保持只读，请使用文件系统权限或单独的 profile/toolset 设置。
- **本地优先**：如果同一个 skill 名称同时存在于本地目录和外部目录中，本地版本优先。
- **完全集成**：外部 skills 出现在系统提示索引、`skills_list`、`skill_view` 中，并作为 `/skill-name` 斜杠命令 — 与本地 skills 没有区别。
- **不存在的路径静默跳过**：如果配置的目录不存在，Hermes 将忽略它而不报错。这对于可能不在每台机器上都存在的可选共享目录很有用。

### 示例

```text
~/.hermes/skills/               # 本地（主要，读写）
├── devops/deploy-k8s/
│   └── SKILL.md
└── mlops/axolotl/
    └── SKILL.md

~/.agents/skills/               # 外部（共享，如可写则可变）
├── my-custom-workflow/
│   └── SKILL.md
└── team-conventions/
    └── SKILL.md
```

所有四个 skills 都出现在你的 skill 索引中。如果你在本地创建一个名为 `my-custom-workflow` 的新 skill，它将覆盖外部版本。

## Skill Bundles（技能包）

Skill bundles 是将多个 skills 组合在单个斜杠命令下的小型 YAML 文件。当你运行 `/<bundle-name>` 时，bundle 中列出的每个 skill 会一次性加载 — 当某个任务总是需要同一组 skills 一起使用时非常有用。

### 快速示例

```bash
# 为后端功能开发创建一个 bundle
hermes bundles create backend-dev \
  --skill github-code-review \
  --skill test-driven-development \
  --skill github-pr-workflow \
  -d "Backend feature work — review, test, PR workflow"
```

然后在 CLI 或任何网关平台中：

```
/backend-dev refactor the auth middleware
```

智能体接收到的是一条用户消息中加载的所有三个 skills，斜杠命令后的任何文本都作为用户指令附加。

### YAML 模式

Bundles 存放在 **`~/.hermes/skill-bundles/<slug>.yaml`** 中，格式如下：

```yaml
name: backend-dev
description: Backend feature work — review, test, PR workflow.
skills:
  - github-code-review
  - test-driven-development
  - github-pr-workflow
instruction: |
  Always start by writing failing tests, then implement.
  Open the PR through the standard workflow with co-author tags.
```

字段：
- `name`（可选 — 默认为文件名主干）— bundle 的显示名称。斜杠命令会规范化为连字符 slug（`Backend Dev` → `/backend-dev`）。
- `description`（可选）— 在 `/bundles` 和 `hermes bundles list` 中显示的简短文本。
- `skills`（必需，非空列表）— skill 名称或相对于 skills 目录的路径。使用与传给 `/<skill-name>` 相同的标识符。
- `instruction`（可选）— 附加到加载的 skill 内容之前的额外指导。适用于固化"我们如何总是组合使用它们"的模式。

### 管理 bundles

```bash
# 列出所有已安装的 bundles
hermes bundles list

# 查看某个 bundle
hermes bundles show backend-dev

# 交互式创建 bundle（省略 --skill 标志则逐行输入）
hermes bundles create research

# 覆盖现有 bundle
hermes bundles create backend-dev --skill ... --force

# 删除一个 bundle
hermes bundles delete backend-dev

# 重新扫描 ~/.hermes/skill-bundles/ 并报告变更
hermes bundles reload
```

在聊天会话中，`/bundles` 列出每个已安装的 bundle 及其 skills。

### 行为

- **当 slug 冲突时，bundles 优先于单个 skills**。如果你将一个 bundle 命名为 `research`，并且同时有一个叫 `research` 的 skill，`/research` 会调用该 bundle。这是有意设计的 — 你通过命名选择了 bundle。
- **缺失的 skills 会被跳过，不会致命。** 如果 bundle 列出了 `skill-foo` 而你未安装它，bundle 仍然会加载能解析到的 skills，智能体会收到一条说明跳过了什么内容的提示。
- **Bundles 在所有界面中都能使用** — 交互式 CLI、TUI、仪表盘聊天以及每个网关平台（Telegram、Discord、Slack 等）— 因为调度与单个 skill 命令在同一位置集中处理。
- **Bundles 不会使提示缓存失效。** 它们在调用时生成一条新的用户消息，与 `/<skill-name>` 的方式相同 — 不会对系统提示做出改动。

### 何时 bundle 比手动安装每个 skill 更好

在以下场景使用 bundle：
- 你总是将相同的 skills 配对用于一个重复性任务（`/backend-dev`、`/release-prep`、`/incident-response`）。
- 你希望拥有比依次输入多个 `/skill` 命令更简洁的心智模型。
- 你希望将团队范围的"任务配置文件"通过将 bundle YAML 签入共享 dotfiles 仓库并符号链接到 `~/.hermes/skill-bundles/` 中来分发。

Bundle 只是一个 YAML 别名 — 它不会为你安装 skills。skills 本身必须已经存在（在 `~/.hermes/skills/` 或外部 skill 目录中）。否则，bundle 调用只会跳过缺失的。

## 智能体管理的 Skills（skill_manage 工具）

智能体可以通过 `skill_manage` 工具创建、更新和删除自己的 skills。这是智能体的**过程性记忆** — 当它摸索出一个非平凡的工作流程时，会将方法保存为 skill 以供将来复用。

### 智能体何时创建 Skills

- 成功完成一个复杂任务（5 次以上工具调用）后
- 当遇到错误或死胡同并找到了有效路径时
- 当用户纠正了其方法时
- 当发现了一个非平凡的工作流程时

### 操作

| 操作 | 用途 | 关键参数 |
|--------|---------|------------|
| `create` | 从头创建新 skill | `name`、`content`（完整 SKILL.md）、可选 `category` |
| `patch` | 针对性修复（推荐） | `name`、`old_string`、`new_string` |
| `edit` | 大规模结构重写 | `name`、`content`（完整 SKILL.md 替换） |
| `delete` | 完全删除一个 skill | `name` |
| `write_file` | 添加/更新辅助文件 | `name`、`file_path`、`file_content` |
| `remove_file` | 删除辅助文件 | `name`、`file_path` |

:::tip
`patch` 操作是推荐的更新方式 — 比 `edit` 更节省 token，因为只有变更的文本出现在工具调用中。
:::

## Skills Hub

浏览、搜索、安装和管理来自在线注册表、`skills.sh`、直接知名 skill 端点以及官方可选 skills 的 skills。

### 常用命令

```bash
hermes skills browse                              # 浏览所有 hub skills（官方优先）
hermes skills browse --source official            # 仅浏览官方可选 skills
hermes skills search kubernetes                   # 搜索所有来源
hermes skills search react --source skills-sh     # 搜索 skills.sh 目录
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect openai/skills/k8s           # 安装前预览
hermes skills install openai/skills/k8s           # 安装并进行安全扫描
hermes skills install official/security/1password
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install https://sharethis.chat/SKILL.md              # 直接 URL（单文件 SKILL.md）
hermes skills install https://example.com/SKILL.md --name my-skill # 当前置元数据中没有名称时覆盖名称
hermes skills list --source hub                   # 列出通过 hub 安装的 skills
hermes skills check                               # 检查已安装的 hub skills 是否有上游更新
hermes skills update                              # 需要时重新安装有上游变更的 hub skills
hermes skills audit                               # 重新扫描所有 hub skills 的安全性
hermes skills uninstall k8s                       # 卸载一个 hub skill
hermes skills reset google-workspace              # 将内置 skill 从"用户已修改"状态恢复（见下文）
hermes skills reset google-workspace --restore    # 同时恢复内置版本，删除你的本地编辑
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json          # 导出 skill 配置
hermes skills tap add myorg/skills-repo           # 添加自定义 GitHub 源
```

### 支持的 hub 来源

| 来源 | 示例 | 说明 |
|--------|---------|-------|
| `official` | `official/security/1password` | 随 Hermes 一起提供的可选 skills。 |
| `skills-sh` | `skills-sh/vercel-labs/agent-skills/vercel-react-best-practices` | 可通过 `hermes skills search <query> --source skills-sh` 搜索。当 skills.sh slug 与仓库文件夹不同时，Hermes 会解析别名式 skills。 |
| `well-known` | `well-known:https://mintlify.com/docs/.well-known/skills/mintlify` | 从网站上的 `/.well-known/skills/index.json` 直接提供的 skills。使用站点或文档 URL 进行搜索。 |
| `url` | `https://sharethis.chat/SKILL.md` | 指向单文件 `SKILL.md` 的直接 HTTP(S) URL。名称解析：前置元数据 → URL slug → 交互式提示 → `--name` 标志。 |
| `github` | `openai/skills/k8s` | 直接 GitHub 仓库/路径安装和自定义 taps。 |
| `clawhub`、`lobehub`、`browse-sh`、`claude-marketplace` | 特定来源标识符 | 社区或市场集成。 |

### 集成的 hubs 和注册表

Hermes 目前集成了以下 skills 生态系统和发现来源：

#### 1. 官方可选 skills（`official`）

这些在 Hermes 仓库自身中维护，以内置信任安装。

- 目录：[官方可选 Skills 目录](../../reference/optional-skills-catalog)
- 仓库中的源：`optional-skills/`
- 示例：

```bash
hermes skills browse --source official
hermes skills install official/security/1password
```

#### 2. skills.sh（`skills-sh`）

这是 Vercel 的公共 skills 目录。Hermes 可以直接搜索它、查看 skill 详情页、解析别名式 slug，并从底层源仓库安装。

- 目录：[skills.sh](https://skills.sh/)
- CLI/工具仓库：[vercel-labs/skills](https://github.com/vercel-labs/skills)
- 官方 Vercel skills 仓库：[vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)
- 示例：

```bash
hermes skills search react --source skills-sh
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
```

#### 3. 知名 skill 端点（`well-known`）

这是从发布 `/.well-known/skills/index.json` 的站点进行的基于 URL 的发现。它不是单一的集中式 hub — 而是一种 Web 发现约定。

- 示例端点：[Mintlify docs skills index](https://mintlify.com/docs/.well-known/skills/index.json)
- 参考服务端实现：[vercel-labs/skills-handler](https://github.com/vercel-labs/skills-handler)
- 示例：

```bash
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
```

#### 4. 直接 GitHub skills（`github`）

Hermes 可以直接从 GitHub 仓库和基于 GitHub 的 taps 安装。当你知道仓库/路径或想添加自己的自定义源仓库时非常有用。

默认 taps（无需任何设置即可浏览）：
- [openai/skills](https://github.com/openai/skills)
- [anthropics/skills](https://github.com/anthropics/skills)
- [huggingface/skills](https://github.com/huggingface/skills)
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)
- [garrytan/gstack](https://github.com/garrytan/gstack)

- 示例：

```bash
hermes skills install openai/skills/k8s
hermes skills tap add myorg/skills-repo
```

#### 5. ClawHub（`clawhub`）

作为社区来源集成的第三方 skills 市场。

- 站点：[clawhub.ai](https://clawhub.ai/)
- Hermes 来源 ID：`clawhub`

#### 6. Claude 市场风格仓库（`claude-marketplace`）

Hermes 支持发布 Claude 兼容插件/市场清单的市场仓库。

已知集成的来源包括：
- [anthropics/skills](https://github.com/anthropics/skills)
- [aiskillstore/marketplace](https://github.com/aiskillstore/marketplace)

Hermes 来源 ID：`claude-marketplace`

#### 7. LobeHub（`lobehub`）

Hermes 可以搜索 LobeHub 公共目录中的智能体条目并将其转换为可安装的 Hermes skills。

- 站点：[LobeHub](https://lobehub.com/)
- 公共智能体索引：[chat-agents.lobehub.com](https://chat-agents.lobehub.com/)
- 后端仓库：[lobehub/lobe-chat-agents](https://github.com/lobehub/lobe-chat-agents)
- Hermes 来源 ID：`lobehub`

#### 8. browse.sh（`browse-sh`）

Hermes 集成了 [browse.sh](https://browse.sh)，这是 Browserbase 的 200 多个特定站点浏览器自动化 SKILL.md 文件目录（Airbnb、Amazon、arXiv、12306.cn、Etsy、Xero 等）。每个 skill 描述了如何端到端地驱动一个网站，适用于 Hermes 的浏览器工具和你已安装的任何浏览器自动化 skills。

- 站点：[browse.sh](https://browse.sh/)
- 目录 API：`https://browse.sh/api/skills`
- Hermes 来源 ID：`browse-sh`
- 信任级别：`community`

```bash
hermes skills search airbnb --source browse-sh
hermes skills inspect browse-sh/airbnb.com/search-listings-ddgioa
hermes skills install browse-sh/airbnb.com/search-listings-ddgioa
```

标识符使用 `browse-sh/<hostname>/<task-id>` 格式，与 browse.sh 目录暴露的 slug 匹配。内容通过每个 skill 的详情端点（`/api/skills/<slug>` → `skillMdUrl`）解析，而不是通过目录的 GitHub `sourceUrl`。

#### 9. 直接 URL（`url`）

从任何 HTTP(S) URL 直接安装单文件 `SKILL.md` — 当作者在自己的网站上托管 skill 时非常有用（没有 hub 列表，没有 GitHub 路径可输入）。Hermes 获取 URL、解析 YAML 前置元数据、安全扫描并安装。

- Hermes 来源 ID：`url`
- 标识符：URL 本身（无需前缀）
- 范围：仅**单文件 `SKILL.md`**。带有 `references/` 或 `scripts/` 的多文件 skills 需要清单，应通过上述其他来源之一发布。

```bash
hermes skills install https://sharethis.chat/SKILL.md
hermes skills install https://example.com/my-skill/SKILL.md --category productivity
```

名称解析，按顺序：
1. SKILL.md YAML 前置元数据中的 `name:` 字段（推荐 — 每个格式正确的 skill 都有）。
2. URL 路径中的父目录名（例如 `.../my-skill/SKILL.md` → `my-skill`，或 `.../my-skill.md` → `my-skill`），当它是有效的标识符时（`^[a-z][a-z0-9_-]*$`）。
3. 在有 TTY 的终端上进行交互式提示。
4. 在非交互界面（TUI 中的 `/skills install` 斜杠命令、网关平台、脚本）上，显示清晰的错误信息，指向 `--name` 覆盖选项。

```bash
# 前置元数据中没有名称，且 URL slug 无帮助 — 手动指定一个：
hermes skills install https://example.com/SKILL.md --name sharethis-chat

# 或在聊天会话中：
/skills install https://example.com/SKILL.md --name sharethis-chat
```

信任级别始终为 `community` — 与所有其他来源运行相同的安全扫描。URL 被存储为安装标识符，因此 `hermes skills update` 会在你想要刷新时自动从同一 URL 重新获取。

### 安全扫描与 `--force`

所有通过 hub 安装的 skills 都经过**安全扫描器**检查，检测数据泄露、提示注入、破坏性命令、供应链信号和其他威胁。

`hermes skills inspect ...` 现在还会在有上游元数据时显示：
- 仓库 URL
- skills.sh 详情页 URL
- 安装命令
- 每周安装量
- 上游安全审计状态
- 知名索引/端点 URL

当你已审查过第三方 skill 并想覆盖非危险性的策略阻止时，使用 `--force`：

```bash
hermes skills install skills-sh/anthropics/skills/pdf --force
```

重要行为：
- `--force` 可以覆盖 caution/warn 级别的策略阻止。
- `--force` **不会**覆盖 `dangerous` 扫描判决。
- 官方可选 skills（`official/...`）被视为内置信任，不显示第三方警告面板。

### 信任级别

| 级别 | 来源 | 策略 |
|-------|--------|--------|
| `builtin` | 随 Hermes 提供 | 始终信任 |
| `official` | 仓库中的 `optional-skills/` | 内置信任，无第三方警告 |
| `trusted` | 受信任的注册表/仓库，如 `openai/skills`、`anthropics/skills`、`huggingface/skills` | 比社区来源更宽松的策略 |
| `community` | 其他所有来源（`skills.sh`、知名端点、自定义 GitHub 仓库、大多数市场） | 非危险性发现可用 `--force` 覆盖；`dangerous` 判决保持阻止 |

### 更新生命周期

Hub 现在跟踪足够的来源信息来重新检查已安装 skills 的上游副本：

```bash
hermes skills check          # 报告哪些已安装的 hub skills 在上游有变更
hermes skills update         # 仅重新安装有可用更新的 skills
hermes skills update react   # 更新一个特定的已安装 hub skill
```

这使用存储的来源标识符加上当前上游 bundle 内容哈希来检测差异。

:::tip GitHub 速率限制
Skills hub 操作使用 GitHub API，对于未认证用户，速率限制为 60 请求/小时。如果在安装或搜索时遇到速率限制错误，请在 `.env` 文件中设置 `GITHUB_TOKEN` 以将限制提高到 5,000 请求/小时。发生此情况时，错误消息会包含可操作的提示。
:::

### 发布自定义 skill tap

如果你想分享一组精选的 skills — 为团队、组织或公开使用 — 可以将它们发布为 **tap**：其他 Hermes 用户通过 `hermes skills tap add <owner/repo>` 添加的 GitHub 仓库。无需服务器、无需注册表注册、无需发布流水线。只需一个包含 `SKILL.md` 文件的目录。

#### 仓库布局

Tap 是任何 GitHub 仓库（公开或私有 — 私有需要 `GITHUB_TOKEN`），布局如下：

```
owner/repo
├── skills/                       # 默认路径；可按 tap 配置
│   ├── my-workflow/
│   │   ├── SKILL.md              # 必需
│   │   ├── references/           # 可选的辅助文件
│   │   ├── templates/
│   │   └── scripts/
│   ├── another-skill/
│   │   └── SKILL.md
│   └── third-skill/
│       └── SKILL.md
└── README.md                     # 可选但推荐
```

规则：
- 每个 skill 位于 tap 根路径（默认 `skills/`）下的独立目录中。
- 目录名成为 skill 的安装 slug。
- 每个 skill 目录必须包含一个 `SKILL.md`，带有标准 [SKILL.md 前置元数据](#skillmd-格式)（`name`、`description`，以及可选的 `metadata.hermes.tags`、`version`、`author`、`platforms`、`metadata.hermes.config`）。
- 子目录如 `references/`、`templates/`、`scripts/`、`assets/` 在安装时随 `SKILL.md` 一起下载。
- 目录名以 `.` 或 `_` 开头的 skill 会被忽略。

Hermes 通过列出 tap 路径的每个子目录并探测每个目录中的 `SKILL.md` 来发现 skills。

#### 最小 tap 示例

```
my-org/hermes-skills
└── skills/
    └── deploy-runbook/
        └── SKILL.md
```

`skills/deploy-runbook/SKILL.md`：

```markdown
---
name: deploy-runbook
description: Our deployment runbook — services, rollback, Slack channels
version: 1.0.0
author: My Org Platform Team
metadata:
  hermes:
    tags: [deployment, runbook, internal]
---

# Deploy Runbook

Step 1: ...
```

推送到 GitHub 后，任何 Hermes 用户都可以订阅并安装：

```bash
hermes skills tap add my-org/hermes-skills
hermes skills search deploy
hermes skills install my-org/hermes-skills/deploy-runbook
```

#### 非默认路径

如果你的 skills 不位于 `skills/` 下（当你在现有项目中添加 `skills/` 子树时很常见），编辑 `~/.hermes/.hub/taps.json` 中的 tap 条目：

```json
{
  "taps": [
    {"repo": "my-org/platform-docs", "path": "internal/skills/"}
  ]
}
```

`hermes skills tap add` CLI 默认新 tap 的路径为 `path: "skills/"`；如需不同路径，请直接编辑文件。`hermes skills tap list` 显示每个 tap 的有效路径。

#### 直接安装单个 skills（无需添加 tap）

用户也可以从任何公共 GitHub 仓库直接安装单个 skill，而无需将整个仓库添加为 tap：

```bash
hermes skills install owner/repo/skills/my-workflow
```

当你想分享一个 skill 而不让用户订阅你的整个注册表时很有用。

#### Taps 的信任级别

新 taps 默认分配 `community` 信任级别。从中安装的 skills 会经过标准安全扫描，并在首次安装时显示第三方警告面板。如果你的组织或广泛信任的来源应获得更高的信任级别，请将其仓库添加到 `tools/skills_hub.py` 中的 `TRUSTED_REPOS`（需要 Hermes 核心 PR）。

#### Tap 管理

```bash
hermes skills tap list                                # 显示所有已配置的 taps
hermes skills tap add myorg/skills-repo               # 添加（默认路径：skills/）
hermes skills tap remove myorg/skills-repo            # 移除
```

在运行中的会话中：

```
/skills tap list
/skills tap add myorg/skills-repo
/skills tap remove myorg/skills-repo
```

Taps 存储在 `~/.hermes/.hub/taps.json` 中（按需创建）。

## 内置 skill 更新（`hermes skills reset`）

Hermes 在仓库的 `skills/` 中随附一组内置 skills。在安装时以及每次 `hermes update` 时，同步过程会将这些内容复制到 `~/.hermes/skills/` 中，并在 `~/.hermes/skills/.bundled_manifest` 中记录一个清单，将每个 skill 名称映射到同步时的内容哈希（**原始哈希**）。

每次同步时，Hermes 重新计算本地副本的哈希并与原始哈希比较：

- **未更改** → 安全地拉取上游更改，复制新的内置版本，记录新的原始哈希。
- **已更改** → 视为**用户已修改**并永久跳过，因此你的编辑永远不会被覆盖。

这种保护很好，但有一个尖锐的边界情况。如果你编辑了一个内置 skill，之后想放弃更改并回到内置版本，只需从 `~/.hermes/hermes-agent/skills/` 复制粘贴，清单仍保留上次成功同步运行时的*旧*原始哈希。你的新复制粘贴内容（当前内置哈希）与该过时的原始哈希不匹配，因此同步会持续将其标记为用户已修改。

`hermes skills reset` 是逃生出口：

```bash
# 安全：清除此 skill 的清单条目。你的当前副本被保留，
# 但下次同步会基于它重新建立基线，以便后续更新正常工作。
hermes skills reset google-workspace

# 完全恢复：同时删除你的本地副本并重新复制当前内置
# 版本。当你想要回纯净的上游 skill 时使用此命令。
hermes skills reset google-workspace --restore

# 非交互式（例如在脚本或 TUI 模式中）— 跳过 --restore 的确认。
hermes skills reset google-workspace --restore --yes
```

相同的命令在聊天中作为斜杠命令使用：

```text
/skills reset google-workspace
/skills reset google-workspace --restore
```

:::note Profiles
每个 profile 在其自身的 `HERMES_HOME` 下有自己的 `.bundled_manifest`，因此 `hermes -p coder skills reset <name>` 只影响该 profile。
:::

### 斜杠命令（聊天内）

所有相同的命令都可以通过 `/skills` 使用：

```text
/skills browse
/skills search react --source skills-sh
/skills search https://mintlify.com/docs --source well-known
/skills inspect skills-sh/vercel-labs/json-render/json-render-react
/skills install openai/skills/skill-creator --force
/skills check
/skills update
/skills reset google-workspace
/skills list
```

官方可选 skills 仍使用诸如 `official/security/1password` 和 `official/migration/openclaw-migration` 的标识符。
