---
title: 工具搜索
sidebar_position: 95
---

# 工具搜索

当你的会话挂载了大量 MCP 服务器或非核心插件工具时，它们的 JSON Schema 会在每次交互中消耗相当大比例的上下文窗口——即使其中只有少数几个与用户的实际请求相关。

**工具搜索（Tool Search）** 是 Hermes 针对此问题提供的可选渐进式披露层。启用后，MCP 和插件工具会被三个桥接工具替换到模型可见的工具数组中，模型仅在需要时按需加载具体工具的 Schema。

:::info Hermes 内置工具不会被延迟加载
构成 Hermes 核心能力集的工具（`terminal`、`read_file`、`write_file`、`patch`、`search_files`、`todo`、`memory`、`browser_*`、`web_search`、`web_extract`、`clarify`、`execute_code`、`delegate_task`、`session_search`、`send_message` 等 `_HERMES_CORE_TOOLS`）**始终**直接加载。只有 MCP 工具和非核心插件工具有资格被延迟加载。
:::

## 工作原理

当工具搜索在某一轮激活时，模型会看到三个新工具替代了被延迟的那些：

```text
tool_search(query, limit?)     — 搜索延迟工具目录
tool_describe(name)            — 加载某个工具的完整 Schema
tool_call(name, arguments)     — 调用某个延迟工具
```

典型的交互流程如下：

```text
模型: tool_search("create a github issue")
  → { matches: [{ name: "mcp_github_create_issue", ... }, ...] }
模型: tool_describe("mcp_github_create_issue")
  → { parameters: { type: "object", properties: { ... } } }
模型: tool_call("mcp_github_create_issue", { title: "...", body: "..." })
  → { ok: true, issue_number: 42 }
```

当模型调用 `tool_call` 时，Hermes **解除桥接**并直接调度底层工具，就好像模型直接调用了该工具一样。工具调用前的 Hook、护栏、审批提示和调用后的 Hook 均针对真实工具名运行——而非 `tool_call`。CLI 和 Gateway 中的活动信息也会解除包装，让你看到底层工具而非桥接器。

## 何时激活？

默认情况下，工具搜索以 `auto` 模式运行：仅当可延迟的工具 Schema 会消耗活动模型上下文窗口至少 **10%** 时才激活。低于该阈值时，工具数组的组装为纯透传模式，不产生额外开销。

这一决策在每次构建工具数组时重新评估，因此：

- 只有少量 MCP 工具且使用长上下文模型的会话永远不会激活工具搜索。
- 挂载了大量 MCP 服务器（通常 15+ 个工具）的会话会开始激活它。
- 中途移除 MCP 服务器后，下次组装时能正确恢复到直接暴露模式。

## 配置

```yaml
tools:
  tool_search:
    enabled: auto       # auto（默认）、on 或 off
    threshold_pct: 10   # 上下文窗口百分比——仅在 auto 模式下使用
    search_default_limit: 5
    max_search_limit: 20
```

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `enabled` | `auto` | `auto` 超过阈值后激活；`on` 只要存在至少一个可延迟工具就始终激活；`off` 完全禁用。 |
| `threshold_pct` | `10` | `auto` 模式触发的上下文长度百分比。范围 0–100。 |
| `search_default_limit` | `5` | 模型未指定 `limit` 时 `tool_search` 返回的匹配数。 |
| `max_search_limit` | `20` | 模型通过 `limit` 参数可请求的硬上限。范围 1–50。 |

你也可以使用传统的布尔值格式：

```yaml
tools:
  tool_search: true   # 等同于 {enabled: auto}
```

## 何时不使用？

工具搜索以固定的每轮 Token 开销（三个桥接工具的 Schema，约 300 Token）和至少一次额外的往返（搜索 → 描述 → 调用）来换取被延迟 Schema 的节省。当你拥有大量工具但每轮只用少量工具时，这是明显的优势；当工具总数较少时则成为额外开销。

`auto` 默认值为你处理了这些判断。如果你无条件设置 `enabled: on`，在小型工具集上会有轻微每轮开销。

## 不可避免的权衡

这些来自提示缓存完整性的不变约束——它们是任何渐进式披露设计的固有特性，而非此实现特有：

- **冷工具需要一次额外往返。** 模型首次需要某个延迟工具时，需要多花一两次模型调用来查找并加载其 Schema。静态侧的 Token 节省是真实的，但部分会在运行时被抵消。
- **延迟 Schema 无缓存优势。** 加载后的 `tool_describe` 结果会进入对话历史（因此在后续轮次中会被缓存），但永远不会从系统提示缓存前缀中受益。
- **模型质量依赖。** 工具搜索假设模型能够为它需要的工具编写合理的搜索查询。较小的模型在这方面表现较差；已发布的数字（Opus 4 上不使用 vs 使用工具搜索，准确率从 49% 提升至 74%）显示了优势，但也说明仍有约 26 个百分点的准确率属于检索失败。
- **工具集编辑会失效缓存。** 在会话中增加或移除工具会改变桥接工具的描述（包含被延迟工具的数量）和目录，因此提示缓存会失效。这与任何工具集编辑的权衡相同。

## 实现细节

- **检索方式：** 对工具名 + 描述 + 参数名进行分词后的 BM25 检索。当 BM25 返回零正分匹配时，回退到工具名的字面子串匹配，以防止零 IDF 退化情况（例如在目录中搜索 `"github"`，而每个工具名都包含 "github"）。
- **目录跨轮次无状态。** 每次组装时从当前工具定义列表重建——无需会话键控的 `Map`。这避免了存储的目录与实时工具注册表不同步的 Bug。
- **目录范围限定于会话的工具集。** `tool_search`、`tool_describe` 和 `tool_call` 只能看到和调用会话实际被授权使用的工具。被限制在工具集子集中的子 Agent、Kanban Worker 或 Gateway 会话无法通过桥接器发现或调用该子集之外的工具——延迟目录是会话自身已启用/禁用工具集中的可延迟部分，而非整个进程注册表。
- **无 JS 沙箱。** Hermes 采用更简单的"结构化工具"模式（search/describe/call 作为普通函数）。其他某些实现提供的 JS 沙箱"代码模式"攻击面较大，我们选择跳过。

## 参见

- `tools/tool_search.py` — 实现代码
- `tests/tools/test_tool_search.py` — 回归测试套件
- 原始实现 PR 中的 `openclaw-tool-search-report` PDF，了解塑造该设计的研究背景
