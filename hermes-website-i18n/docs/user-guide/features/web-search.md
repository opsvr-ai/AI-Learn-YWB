---
title: 网页搜索与提取
description: 使用多种后端提供商搜索网页、提取页面内容并抓取网站——包括免费的自托管 SearXNG。
sidebar_label: 网页搜索
sidebar_position: 6
---

# 网页搜索与提取

Hermes Agent 包含两个可由模型调用的网页工具，由多个提供商支持：

- **`web_search`** — 搜索网页并返回排序后的结果
- **`web_extract`** — 从一个或多个 URL 获取并提取可读内容（当后端提供时，内置深度抓取支持）

两者通过单一后端选择进行配置。提供商通过 `hermes tools` 选择或直接在 `config.yaml` 中设置。递归抓取功能（Firecrawl/Tavily）通过 `web_extract` 暴露，而非作为单独的 `web_crawl` 工具。

## 后端

| 提供商 | 环境变量 | 搜索 | 提取 | 抓取 | 免费额度 |
|----------|---------|--------|---------|-------|-----------|
| **Firecrawl**（默认） | `FIRECRAWL_API_KEY` | ✔ | ✔ | ✔ | 500 credits/月 |
| **SearXNG** | `SEARXNG_URL` | ✔ | — | — | ✔ 免费（自托管） |
| **Brave Search（免费版）** | `BRAVE_SEARCH_API_KEY` | ✔ | — | — | 2,000 次查询/月 |
| **DDGS (DuckDuckGo)** | —（无需密钥） | ✔ | — | — | ✔ 免费 |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | ✔ | 1,000 次搜索/月 |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | — | 1,000 次搜索/月 |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | — | 付费 |
| **xAI (Grok)** | `XAI_API_KEY` 或 `hermes auth login xai-oauth` | ✔ | — | — | 付费（SuperGrok 或按 token 计费） |

Brave Search、DDGS 和 xAI **仅支持搜索**——当您还需要 `web_extract` 时，将它们与 Firecrawl/Tavily/Exa/Parallel 中的任意一个搭配使用。DDGS 底层使用 [`ddgs` Python 包](https://pypi.org/project/ddgs/)；如果尚未安装，请运行 `pip install ddgs`（或让 Hermes 在首次使用时延迟安装）。xAI 在 Responses API 上运行 Grok 的服务端 `web_search` 工具——结果由 LLM 生成而非基于索引，因此标题、描述和 URL 选择均为模型输出（参见下方的[信任模型说明](#xai-grok)）。

**按能力拆分：** 您可以独立地为搜索和提取使用不同的提供商——例如使用 SearXNG（免费）进行搜索，使用 Firecrawl 进行提取。请参阅下方的[按能力配置](#per-capability-configuration)。

:::tip Nous 订阅用户
如果您拥有付费的 [Nous Portal](https://portal.nousresearch.com) 订阅，网页搜索和提取可通过 **[Tool Gateway](tool-gateway.md)** 经由托管 Firecrawl 使用——无需 API Key。运行 `hermes tools` 即可启用。
:::

---

## `web_extract` 如何处理长页面

后端返回原始页面 Markdown，内容可能非常庞大（论坛帖子、文档站点、带嵌入式评论的新闻文章）。为了保持上下文窗口可用并降低成本，`web_extract` 在将返回内容交给 agent 之前，会通过 **`web_extract` 辅助模型**进行处理。行为完全由内容大小驱动：

| 页面大小（字符数） | 处理方式 |
|------------------------|--------------|
| 低于 5,000 | 原样返回——无需 LLM 调用，完整 Markdown 直接送达 agent |
| 5,000 – 500,000 | 通过 `web_extract` 辅助模型进行单遍摘要，输出上限约 5,000 字符 |
| 500,000 – 2,000,000 | 分块处理：拆分为 100k 字符的块，并行摘要每个块，然后合成最终摘要（约 5,000 字符） |
| 超过 2,000,000 | 拒绝处理，提示使用 `web_crawl` 并配合针对性的提取指令或更具体的来源 |

摘要保留原始格式中的引用、代码块和关键事实——它是一个内容压缩器，而非改写器。如果摘要生成失败或超时，Hermes 会回退到原始内容的前约 5,000 字符，而非返回无用的错误信息。

### 哪个模型负责摘要？

`web_extract` 辅助任务。默认情况下（`auxiliary.web_extract.provider: "auto"`），使用的是您的**主聊天模型**——与 `hermes model` 相同的提供商和模型。这对于大多数配置来说没问题，但在使用昂贵的推理模型（Opus、MiniMax M2.7 等）时，每次长页面提取都会增加显著的成本。

要将提取摘要路由到廉价、快速的模型（无论主模型如何设置）：

```yaml
# ~/.hermes/config.yaml
auxiliary:
  web_extract:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 360       # 秒；如果遇到摘要超时，可调高此值
```

或通过交互方式选择：`hermes model` → **Configure auxiliary models** → `web_extract`。

请参阅[辅助模型](/docs/user-guide/configuration#auxiliary-models)获取完整参考和按任务覆盖的模式。

### 当摘要功能造成阻碍时

如果您特别需要原始的、未经摘要的页面内容——例如，您正在抓取一个结构化页面，而 LLM 摘要会丢失重要字段——请改用 `browser_navigate` + `browser_snapshot`。浏览器工具返回实时无障碍树，无需辅助模型重写（但在超大页面上有其自身的 8,000 字符快照上限）。

---

## 设置

### 通过 `hermes tools` 快速设置

运行 `hermes tools`，导航到 **Web Search & Extract**，然后选择一个提供商。向导会提示输入所需的 URL 或 API Key，并将其写入您的配置。

```bash
hermes tools
```

---

### Firecrawl（默认）

功能齐全的搜索、提取和抓取。推荐大多数用户使用。

```bash
# ~/.hermes/.env
FIRECRAWL_API_KEY=fc-your-key-here
```

在 [firecrawl.dev](https://firecrawl.dev) 获取密钥。免费额度为 500 credits/月。

**自托管 Firecrawl：** 指向您自己的实例而非云 API：

```bash
# ~/.hermes/.env
FIRECRAWL_API_URL=http://localhost:3002
```

当设置了 `FIRECRAWL_API_URL` 时，API Key 为可选（通过 `USE_DB_AUTHENTICATION=false` 禁用服务器认证）。

---

### SearXNG（免费，自托管）

SearXNG 是一个尊重隐私的开源元搜索引擎，聚合来自 70 多个搜索引擎的结果。**无需 API Key**——只需将 Hermes 指向一个运行中的 SearXNG 实例即可。

SearXNG **仅支持搜索**——`web_extract`（包括其抓取模式）需要单独的提取提供商。

#### 方案 A —— 使用 Docker 自托管（推荐）

这样您将拥有一个无速率限制的私有实例。

**1. 创建工作目录：**

```bash
mkdir -p ~/searxng/searxng
cd ~/searxng
```

**2. 编写 `docker-compose.yml`：**

```yaml
# ~/searxng/docker-compose.yml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8888:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8888/
    restart: unless-stopped
```

**3. 启动容器：**

```bash
docker compose up -d
```

**4. 启用 JSON API 格式：**

SearXNG 默认禁用 JSON 输出。复制生成的配置并启用它：

```bash
# 将自动生成的配置从容器中复制出来
docker cp searxng:/etc/searxng/settings.yml ~/searxng/searxng/settings.yml
```

打开 `~/searxng/searxng/settings.yml`，找到 `formats` 块（约第 84 行）：

```yaml
# 修改前（默认 —— JSON 已禁用）：
formats:
  - html

# 修改后（为 Hermes 启用 JSON）：
formats:
  - html
  - json
```

**5. 重启以应用更改：**

```bash
docker cp ~/searxng/searxng/settings.yml searxng:/etc/searxng/settings.yml
docker restart searxng
```

**6. 验证是否正常工作：**

```bash
curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"results\"])} results')"
```

您应该看到类似 `10 results` 的输出。如果收到 `403 Forbidden`，说明 JSON 格式仍然被禁用——请重新检查第 4 步。

**7. 配置 Hermes：**

```bash
# ~/.hermes/.env
SEARXNG_URL=http://localhost:8888
```

然后在 `~/.hermes/config.yaml` 中选择 SearXNG 作为搜索后端：

```yaml
web:
  search_backend: "searxng"
```

或通过 `hermes tools` → Web Search & Extract → SearXNG 设置。

---

#### 方案 B —— 使用公共实例

公共 SearXNG 实例列在 [searx.space](https://searx.space/) 上。按已**启用 JSON 格式**的实例进行筛选（表格中有显示）。

```bash
# ~/.hermes/.env
SEARXNG_URL=https://searx.example.com
```

:::caution 公共实例
公共实例存在速率限制、可用性不稳定，并且可能随时禁用 JSON 格式。对于生产环境使用，强烈建议自托管。
:::

---

#### 将 SearXNG 与提取提供商搭配使用

SearXNG 处理搜索；您需要一个单独的提供商来进行 `web_extract`（包括任何深度抓取模式）。使用按能力配置的键：

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"   # 或 tavily, exa, parallel
```

使用此配置，Hermes 将所有搜索查询交由 SearXNG 处理，将 URL 提取交由 Firecrawl 处理——将免费搜索与高质量提取相结合。

---

### Tavily

AI 优化的搜索、提取和抓取，拥有慷慨的免费额度。

```bash
# ~/.hermes/.env
TAVILY_API_KEY=tvly-your-key-here
```

在 [app.tavily.com](https://app.tavily.com/home) 获取密钥。免费额度为 1,000 次搜索/月。

---

### Exa

具有语义理解能力的神经搜索。适合研究和查找概念上相关的内容。

```bash
# ~/.hermes/.env
EXA_API_KEY=your-exa-key-here
```

在 [exa.ai](https://exa.ai) 获取密钥。免费额度为 1,000 次搜索/月。

---

### Parallel

具有深度研究能力的 AI 原生搜索和提取。

```bash
# ~/.hermes/.env
PARALLEL_API_KEY=your-parallel-key-here
```

在 [parallel.ai](https://parallel.ai) 获取访问权限。

---

### xAI (Grok) {#xai-grok}

在 Responses API 上通过 Grok 的服务端 [web_search 工具](https://docs.x.ai/developers/tools/web-search) 路由 `web_search`。Grok 执行实际搜索并将顶部结果作为结构化 JSON 返回。

支持两种凭据方式——无需新的环境变量，无需新的设置向导：

```bash
# ~/.hermes/.env（环境变量方式）
XAI_API_KEY=sk-xai-your-key-here
```

或针对 SuperGrok 订阅用户：

```bash
hermes auth login xai-oauth
```

然后将 xAI 选为搜索后端：

```yaml
# ~/.hermes/config.yaml
web:
  backend: "xai"
```

**可选配置项：**

```yaml
web:
  backend: "xai"
  xai:
    model: grok-4.3              # web_search 要求的推理模型（默认值）
    allowed_domains:             # 可选，最多 5 个 —— 与 excluded_domains 互斥
      - arxiv.org
    excluded_domains:            # 可选，最多 5 个
      - example-spam.com
    timeout: 90                  # 秒（默认值）
```

**仅限搜索**——如果您还需要 `web_extract`，请搭配 Firecrawl / Tavily / Exa / Parallel。遇到 401 时，提供商会执行一次强制 OAuth token 刷新并重试（覆盖窗口期中的吊销以及主动过期检查无法解码的不透明 token）；使用环境变量凭据时跳过重试。

:::caution 信任模型
与返回逐字搜索引擎结果的基于索引的提供商（Brave、Tavily、Exa）不同，xAI 是一个自行选择展示哪些 URL 并自行撰写标题和描述的 LLM。查询的*内容*会影响输出，因此恶意构造的查询（例如通过 agent 获取的不可信上游输入注入的查询）原则上可能引导 Grok 输出攻击者选择的 URL。将返回的 URL 与任何模型生成的链接同等对待——在获取之前进行验证，尤其是当查询来自不可信输入时。
:::

---

## 配置

### 单一后端

为所有网页功能设置一个提供商：

```yaml
# ~/.hermes/config.yaml
web:
  backend: "searxng"   # firecrawl | searxng | brave-free | ddgs | tavily | exa | parallel | xai
```

### 按能力配置

为搜索和提取使用不同的提供商。这使您能够将免费搜索（SearXNG）与付费提取提供商相结合，反之亦然：

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"     # 由 web_search 使用
  extract_backend: "firecrawl"  # 由 web_extract（及其深度抓取模式）使用
```

当按能力配置的键为空时，两者均回退到 `web.backend`。当 `web.backend` 也为空时，后端会根据存在的 API Key/URL 自动检测。

**优先级顺序（按能力）：**
1. `web.search_backend` / `web.extract_backend`（显式按能力配置）
2. `web.backend`（共享回退）
3. 从环境变量自动检测

### 自动检测

如果没有显式配置后端，Hermes 会根据已设置的凭据选择第一个可用的：

| 存在的凭据 | 自动选择的后端 |
|--------------------|-----------------------|
| `FIRECRAWL_API_KEY` 或 `FIRECRAWL_API_URL` | firecrawl |
| `PARALLEL_API_KEY` | parallel |
| `TAVILY_API_KEY` | tavily |
| `EXA_API_KEY` | exa |
| `SEARXNG_URL` | searxng |

xAI Web Search **不**在自动检测链中——设置了 `XAI_API_KEY`（或通过 xAI Grok OAuth 登录）不会自动将网页流量路由到 xAI，因为这些凭据也用于推理 / TTS / 图像生成，用户可能希望为网页使用不同的后端。需通过 `web.backend: "xai"` 显式选择。

---

## 验证您的设置

运行 `hermes setup` 查看检测到的网页后端：

```
✅ Web Search & Extract (searxng)
```

或通过 CLI 检查：

```bash
# 激活 venv 并直接运行 web tools 模块
source ~/.hermes/hermes-agent/.venv/bin/activate
python -m tools.web_tools
```

这将打印活动的后端及其状态：

```
✅ Web backend: searxng
   Using SearXNG (search only): http://localhost:8888
```

---

## 故障排除

### `web_search` 返回 `{"success": false}`

- 检查 `SEARXNG_URL` 是否可达：`curl -s "http://localhost:8888/search?q=test&format=json"`
- 如果收到 HTTP 403，说明 JSON 格式已被禁用——在 `settings.yml` 的 `formats` 列表中添加 `json` 并重启
- 如果收到连接错误，容器可能未运行：`docker ps | grep searxng`

### `web_extract` 提示 "search-only backend"

SearXNG 无法提取 URL 内容。将 `web.extract_backend` 设置为支持提取的提供商：

```yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"  # 或 tavily / exa / parallel
```

### SearXNG 返回 0 条结果

某些公共实例禁用了某些搜索引擎或类别。尝试：
- 换一个不同的查询
- 从 [searx.space](https://searx.space/) 换一个不同的公共实例
- 自托管您自己的实例以获得可靠的结果

### 在公共实例上遇到速率限制

切换到自托管实例（参见上方的[方案 A](#方案-a--使用-docker-自托管推荐)）。使用 Docker，您自己的实例没有速率限制。

### `web_extract` 返回截断内容并带有 "summarization timed out" 提示

辅助模型未能在配置的超时时间内完成摘要。可以采取以下措施之一：

- 在 `config.yaml` 中调高 `auxiliary.web_extract.timeout`（全新安装默认 360 秒，缺少该键时默认 30 秒）
- 将 `web_extract` 辅助任务切换到更快的模型（例如 `google/gemini-3-flash-preview`）——参见 [`web_extract` 如何处理长页面](#web_extract-如何处理长页面)
- 对于摘要不是正确工具的页面，改用 `browser_navigate`

---

## 可选 skill：`searxng-search`

对于需要通过 `curl` 直接使用 SearXNG 的 agent（例如在 web 工具集不可用时作为回退），请安装 `searxng-search` 可选 skill：

```bash
hermes skills install official/research/searxng-search
```

这会添加一个 skill，教 agent 如何：
- 通过 `curl` 或 Python 调用 SearXNG JSON API
- 按类别筛选（`general`、`news`、`science` 等）
- 处理分页和错误情况
- 在 SearXNG 不可达时优雅地回退
