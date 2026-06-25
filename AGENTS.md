# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

公司内部培训网站："AI赋能日常工作"，纯静态HTML站点，浏览器直接打开即可使用，无需服务器。

## 技术栈

- 纯HTML5 + CSS3 + 原生JavaScript，无构建工具，无框架依赖
- 浅色主题，蓝色系主色调，现代简约卡片式布局
- 桌面端优先，不做响应式适配

## 页面结构（5页 + 公共资源）

| 文件 | 内容 |
|---|---|
| `index.html` | 首页：Hero区、两大工具对比表、三步快速开始 |
| `hermes.html` | Hermes-Agent：环境准备(Python安装+一键脚本)、Skills安装、使用方法、核心功能（报告编写/日常运维/合同相关/写材料）、延伸阅读 |
| `Codex.html` | Codex：Node.js安装(前置条件)、安装配置、开发模式详解(Plan/Auto/讲解/学习)、子代理系统、常用命令、质量保障、延伸阅读 |
| `ai-basics.html` | 大模型基础知识：LLM基础、Prompt工程、Function Call、MCP、Agent、A2A/Skills |
| `api-key.html` | API Key申请指南（已对接实际平台流程和截图） |
| `css/style.css` | 全部样式（CSS变量、导航、卡片、表格、Tab、步骤、折叠、代码块、Lightbox） |
| `js/main.js` | 公共交互（导航高亮、回到顶部、Tab切换、Accordion、代码复制、CMD/PowerShell Tab切换、图片Lightbox） |

**重要**：导航栏在每个 HTML 文件中重复。修改导航时需同步更新所有 5 个主页面 + `hermes-docs/` 下的所有页面。

## 资源目录结构

```
images/                     # 所有截图，英文文件名
├── python-appstore-search.png
├── python-install-link.png
├── token-management.png
├── token-application.png
├── api-interface.png
├── model-catalog.png
├── node-env-settings.png
└── node-version-verify.png
packages/                   # 安装包及配置文件
├── skills.zip
├── node-v24.16.0-win-x64.zip
├── node-v24.16.0-linux-x64.tar.xz
├── settings.json            # Codex 配置模板（Token 已替换为占位符）
tutorials/                  # PDF教程
├── hermes-agent-guide.pdf
├── Codex-beginner.pdf
├── Codex-definitive.pdf
├── Codex-skills.pdf
└── Codex-explore.pdf
素材/                       # 原始素材（临时存放，不直接引用）
```


## Python 脚本

| 文件 | 用途 |
|---|---|
| `server.py` | 本地 HTTP 服务器，支持多线程、HTTP Range（视频拖拽）、打卡 API。绑定 `0.0.0.0:8080`（局域网可访问，便于内部分享） |
| `translate_docs.py` | 批量翻译脚本，调用内网 AI Gateway 将英文文档翻译为中文 |

## 内网地址变更检查清单

若 AI Gateway IP 变更，需同步修改以下所有位置：

| 文件 | 位置说明 |
|---|---|
| `api-key.html` | 第 96-97 行（接口 URL），第 122 行（环境变量示例） |
| `Codex.html` | 第 382 行（说明文字），第 421 行（配置表） |
| `packages/settings.json` | `ANTHROPIC_BASE_URL` 字段 |
| `素材/Codex/settings.json` | `ANTHROPIC_BASE_URL` 字段 |
| `translate_docs.py` | 第 9 行 `API_BASE` 变量 |

> 搜索命令：`grep -rn "7\.24\.28\.9" --include="*.html" --include="*.py" --include="*.json"`


所有页面共用相同的导航栏，采用**下拉菜单模式**便于扩展：

```
首页 | AI赋能日常工作 ▾
             ├ Hermes-Agent
             ├ Codex
             ├ ──────────
             ├ 大模型基础
             ├ API Key 申请
             └ Hermes 官方文档
```

后续新增培训主题时，在 `.nav-links` 中新增 `<li class="has-submenu">` 即可，无需横向扩展。

## 编码注意事项

- CSS中常出现异常字符混入（如中文词片断、`iat`、`else`、`mero`等），是Windows下编码问题，需要检查并修复
- 所有HTML文件使用 `charset="UTF-8"`
- 图片引用使用 `images/` 目录，英文文件名：`<img src="images/token-management.png">`
- 安装包放在 `packages/` 目录：`<a href="packages/skills.zip" download>`
- PDF教程放在 `tutorials/` 目录
- 图片点击自动放大：JS 自动检测 `src` 包含 `/images/` 的 `<img>`，点击弹出 lightbox。无需手动添加类名
- 代码复制：`.code-block` 内嵌 `.copy-btn`，通过 `copyCode(blockId, btn)` 函数实现

## 交互组件用法

### Tab 切换
```html
<div class="tabs">
  <button class="tab-btn active" data-tab="tab-id">标签名</button>
</div>
<div class="tab-panel active" data-tab="tab-id">内容</div>
```

### Accordion 折叠
```html
<div class="accordion">
  <div class="accordion-item">
    <button class="accordion-trigger">标题 <span class="arrow">&#9654;</span></button>
    <div class="accordion-content">内容</div>
  </div>
</div>
```

### 步骤列表
```html
<ol class="steps">
  <li><h4>步骤标题</h4><p>描述</p></li>
</ol>
```

### 代码块（带终端Tab切换）
`switchCodeTab` 和 `copyCode` 通过 `onclick` 属性内联调用，是 JS 中定义的全局函数。

```html
<div class="code-tabs">
  <button class="code-tab active" onclick="switchCodeTab('cmd', this)">CMD</button>
  <button class="code-tab" onclick="switchCodeTab('powershell', this)">PowerShell</button>
</div>
<div id="code-cmd" class="code-block">
  <button class="copy-btn" onclick="copyCode('code-cmd', this)">复制</button>
  命令内容...
</div>
```

## 其他可用样式组件

以下 CSS 类已定义在 style.css 中，可直接使用，无需额外 JS：

- **`.highlight-box`** — 蓝紫渐变背景的突出信息框，用于核心定位/关键说明
- **`.tip`** — 蓝色左边框提示框，`.tip.warning` 为橙色警告变体
- **`.feature-row`** / `.feature-row.reverse` — 图文并排布局（flex，`reverse` 将图放左侧）
- **`.feature-img img`** — feature-row 中的图片容器，自带圆角和阴影
- **`.page-header`** — 子页面顶部标题区（含 `.breadcrumb` 面包屑导航）
- **`.card`** + **`.card-icon`**（`.blue` / `.green` / `.orange` / `.purple`）— 卡片组件
- **`.compare-table`** — 对比表格（首页两大工具对比）
- **`.grid-2` / `.grid-3` / `.grid-4`** — CSS Grid 布局
- **`.btn`**（`.btn-primary` / `.btn-outline` / `.btn-lg` / `.btn-sm`）— 按钮系列
- **`.section`** / **`.section-gray`** — 页面分区，`.section-gray` 有白色背景和边框
- **`.text-center` / `.mt-2` / `.mt-3` / `.mt-4` / `.mb-2` / `.mb-3` / `.mb-4`** — 工具类
