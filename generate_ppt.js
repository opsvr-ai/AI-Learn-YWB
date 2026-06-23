const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "生产运维部";
pres.title = "AI赋能日常工作 - 学习培训";

// ── Color Palette ──
const C = {
  navy:    "0F172A",
  dkBlue:  "1E3A5F",
  blue:    "2563EB",
  ltBlue:  "DBEAFE",
  ice:     "EFF6FF",
  white:   "FFFFFF",
  offWht:  "F8FAFC",
  dkText:  "1E293B",
  gray:    "64748B",
  ltGray:  "CBD5E1",
  green:   "059669",
  orange:  "EA580C",
  purple:  "7C3AED",
  cyan:    "0891B2",
  amber:   "FEF3C7",
  codeBg:  "1E293B",
  codeTx:  "E2E8F0",
  red:     "DC2626",
};

// ── Helpers ──
const makeShadow = () => ({ type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.08 });

function addSlideNum(slide, num) {
  slide.addText(String(num), { x: 9.2, y: 5.05, w: 0.6, h: 0.4, fontSize: 9, color: C.gray, align: "right", fontFace: "Calibri" });
}

function sectionDivider(number, title, subtitle) {
  const s = pres.addSlide();
  s.background = { color: C.navy };
  // Decorative circle
  s.addShape(pres.shapes.OVAL, { x: 7.5, y: -1.5, w: 5, h: 5, fill: { color: C.dkBlue, transparency: 40 } });
  s.addShape(pres.shapes.OVAL, { x: 8.5, y: 2.5, w: 3, h: 3, fill: { color: C.dkBlue, transparency: 60 } });
  // Number
  s.addText(String(number).padStart(2,"0"), { x: 0.8, y: 1.2, w: 2, h: 1.5, fontSize: 60, fontFace: "Arial Black", color: C.blue, bold: true });
  // Accent line
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.9, w: 1.2, h: 0.06, fill: { color: C.blue } });
  // Title & subtitle
  s.addText(title, { x: 0.8, y: 3.2, w: 8, h: 0.8, fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true });
  s.addText(subtitle, { x: 0.8, y: 4.0, w: 7, h: 0.5, fontSize: 14, fontFace: "Calibri", color: C.gray });
  return s;
}

function card(slide, x, y, w, h, icon, title, body, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.white }, shadow: makeShadow() });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h, fill: { color: accentColor || C.blue } });
  slide.addText(icon, { x: x+0.2, y: y+0.15, w: 0.5, h: 0.5, fontSize: 22, align: "center", fontFace: "Calibri" });
  slide.addText(title, { x: x+0.2, y: y+0.65, w: w-0.4, h: 0.4, fontSize: 12, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });
  slide.addText(body, { x: x+0.2, y: y+1.0, w: w-0.4, h: h-1.2, fontSize: 9.5, fontFace: "Calibri", color: C.gray, valign: "top", margin: 0 });
}

function codeBlock(slide, x, y, w, h, text) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.codeBg }, shadow: makeShadow() });
  const lines = text.trim().split("\n");
  const content = lines.map((line, i) => {
    const opts = { fontSize: 8, fontFace: "Consolas", color: C.codeTx, margin: 0 };
    if (i < lines.length - 1) opts.breakLine = true;
    return { text: line, options: opts };
  });
  slide.addText(content, { x: x+0.2, y: y+0.15, w: w-0.4, h: h-0.3, valign: "top", margin: 0 });
}

function tipBox(slide, x, y, w, text, type) {
  const bg = type === "warn" ? C.amber : C.ice;
  const border = type === "warn" ? C.orange : C.blue;
  const icon = type === "warn" ? "!" : "i";
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.55, fill: { color: bg } });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 0.55, fill: { color: border } });
  slide.addShape(pres.shapes.OVAL, { x: x+0.15, y: y+0.1, w: 0.35, h: 0.35, fill: { color: border } });
  slide.addText(icon, { x: x+0.15, y: y+0.1, w: 0.35, h: 0.35, fontSize: 12, color: C.white, align: "center", fontFace: "Arial Black", margin: 0 });
  slide.addText(text, { x: x+0.6, y: y+0.08, w: w-0.75, h: 0.4, fontSize: 9.5, fontFace: "Calibri", color: C.dkText, margin: 0 });
}

// ═══════════════════════════════════════════
// SLIDE 1: COVER
// ═══════════════════════════════════════════
let s1 = pres.addSlide();
s1.background = { color: C.navy };
s1.addShape(pres.shapes.OVAL, { x: 6.5, y: -2, w: 6, h: 6, fill: { color: C.dkBlue, transparency: 30 } });
s1.addShape(pres.shapes.OVAL, { x: 8, y: 2, w: 4, h: 4, fill: { color: C.dkBlue, transparency: 50 } });
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.navy, transparency: 30 } });
// Badge
s1.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.2, w: 1.8, h: 0.38, fill: { color: C.blue } });
s1.addText("TRAINING 2026", { x: 0.8, y: 1.2, w: 1.8, h: 0.38, fontSize: 9, fontFace: "Arial Black", color: C.white, align: "center", charSpacing: 3, margin: 0 });
// Title
s1.addText("AI赋能\n日常工作", { x: 0.8, y: 1.8, w: 8, h: 2.0, fontSize: 48, fontFace: "Arial Black", color: C.white, bold: true, lineSpacingMultiple: 1.1 });
// Accent
s1.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 3.9, w: 0.8, h: 0.06, fill: { color: C.blue } });
// Subtitle
s1.addText("人工智能工具学习培训", { x: 0.8, y: 4.15, w: 5, h: 0.4, fontSize: 16, fontFace: "Calibri", color: C.gray });
s1.addText("生产运维部 · 内部培训资料", { x: 0.8, y: 4.55, w: 5, h: 0.35, fontSize: 11, fontFace: "Calibri", color: C.gray });

// ═══════════════════════════════════════════
// SLIDE 2: AGENDA
// ═══════════════════════════════════════════
let s2 = pres.addSlide();
s2.background = { color: C.offWht };
s2.addText("目  录", { x: 0.8, y: 0.4, w: 4, h: 0.7, fontSize: 32, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });
s2.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.1, w: 0.6, h: 0.05, fill: { color: C.blue } });

const agenda = [
  ["01", "平台概述", "两大工具对比、三步快速开始"],
  ["02", "Hermes-Agent 指南", "环境准备、安装配置、Skills、使用方法"],
  ["03", "Claude Code 指南", "Node.js安装、安装配置、常用命令"],
  ["04", "大模型基础知识", "LLM、Prompt工程、Function Call、MCP、Agent"],
  ["05", "API Key 申请", "申请流程、令牌管理、常见问题"],
];
agenda.forEach((item, i) => {
  const y = 1.6 + i * 0.72;
  s2.addShape(pres.shapes.RECTANGLE, { x: 0.8, y, w: 8.4, h: 0.6, fill: { color: i%2===0 ? C.white : C.offWht } });
  s2.addText(item[0], { x: 0.8, y, w: 0.8, h: 0.6, fontSize: 22, fontFace: "Arial Black", color: C.blue, align: "center", margin: 0 });
  s2.addShape(pres.shapes.RECTANGLE, { x: 1.6, y: y+0.1, w: 0.04, h: 0.4, fill: { color: C.ltGray } });
  s2.addText(item[1], { x: 1.8, y: y+0.05, w: 3, h: 0.3, fontSize: 14, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });
  s2.addText(item[2], { x: 1.8, y: y+0.32, w: 5, h: 0.25, fontSize: 10, fontFace: "Calibri", color: C.gray, margin: 0 });
});
addSlideNum(s2, 2);

// ═══════════════════════════════════════════
// CH1: 平台概述
// ═══════════════════════════════════════════
sectionDivider("01", "平台概述", "两大核心工具对比 · 三步快速开始 · 使用场景速查");

// Slide: 两大工具对比
let s3 = pres.addSlide();
s3.background = { color: C.offWht };
s3.addText("两大核心工具对比", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });
s3.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 0.9, w: 0.5, h: 0.04, fill: { color: C.blue } });

const rows = [
  [{ text: "对比维度", options: { bold: true, color: C.white, fill: { color: C.blue }, fontSize: 10, fontFace: "Arial Black" } },
   { text: "Hermes-Agent", options: { bold: true, color: C.white, fill: { color: C.blue }, fontSize: 10, fontFace: "Arial Black" } },
   { text: "Claude Code", options: { bold: true, color: C.white, fill: { color: C.blue }, fontSize: 10, fontFace: "Arial Black" } }],
  ["定  位", "对话式AI智能助手", "终端AI编程协作工具"],
  ["目标用户", "生产运维部全员", "开发工程师"],
  ["核心能力", "日常办公、文档处理、报告编写", "代码开发、调试、Code Review"],
  ["运行环境", "终端/TUI/桌面端", "命令行终端"],
  ["接口类型", "OpenAI兼容接口", "Anthropic原生接口"],
  ["推荐模型", "Qwen3.6-35B-A3B", "Claude系列"],
  ["学习难度", "低，开箱即用", "中，需基础命令行知识"],
  ["安装前提", "Python 3.11+", "Node.js 24+"],
];
const tableData = rows.map((r, ri) => r.map((c, ci) => {
  const base = { fontSize: 9, fontFace: "Calibri", color: C.dkText, valign: "middle" };
  if (typeof c === "string") return { text: c, options: { ...base, fill: { color: ri%2===0 ? C.white : C.offWht } } };
  return { text: c.text, options: { ...base, ...c.options } };
}));
s3.addTable(tableData, { x: 0.6, y: 1.15, w: 8.8, colW: [1.4, 3.7, 3.7], rowH: [0.42, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42], border: { pt: 0.5, color: C.ltGray } });

// Scenario cards
card(s3, 0.6, 5.0, 4.2, 0.5, "📋", "日常办公 → Hermes-Agent", "写报告、写邮件、文档处理、数据分析", C.blue);
card(s3, 5.2, 5.0, 4.2, 0.5, "💻", "代码开发 → Claude Code", "编程、调试、Code Review、架构设计", C.purple);
addSlideNum(s3, 3);

// Slide: 三步快速开始
let s4 = pres.addSlide();
s4.background = { color: C.white };
s4.addText("三步快速开始", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

for (let i = 0; i < 3; i++) {
  const y = 1.3 + i * 1.35;
  const steps = [
    { num: "1", icon: "🔑", title: "申请 API Key", desc: "访问 AI Gateway 平台 (aigateway.sccba.org)\n使用域账号登录，申请个人令牌\n提交后联系康龙雨审批" },
    { num: "2", icon: "📦", title: "安装工具", desc: "全员 → 安装 Hermes-Agent (Python)\n开发 → 安装 Claude Code (Node.js)\n复制一键安装脚本到终端执行" },
    { num: "3", icon: "🚀", title: "开始使用", desc: "配置 API Key 到工具中\n启动工具，开始与 AI 对话\n逐步探索 Skills、MCP 等高级功能" },
  ];
  const step = steps[i];
  s4.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 8.8, h: 1.15, fill: { color: i===0 ? C.ice : C.offWht }, shadow: i===0 ? makeShadow() : undefined });
  s4.addShape(pres.shapes.OVAL, { x: 0.85, y: y+0.25, w: 0.65, h: 0.65, fill: { color: i===0 ? C.blue : C.ltGray } });
  s4.addText(step.num, { x: 0.85, y: y+0.25, w: 0.65, h: 0.65, fontSize: 28, fontFace: "Arial Black", color: i===0 ? C.white : C.gray, align: "center", margin: 0 });
  s4.addText(step.icon + "  " + step.title, { x: 1.8, y: y+0.1, w: 6, h: 0.4, fontSize: 16, fontFace: "Arial Black", color: C.dkText, margin: 0 });
  s4.addText(step.desc, { x: 1.8, y: y+0.5, w: 7, h: 0.55, fontSize: 10, fontFace: "Calibri", color: C.gray, margin: 0 });
}
addSlideNum(s4, 4);

// ═══════════════════════════════════════════
// CH2: Hermes-Agent
// ═══════════════════════════════════════════
sectionDivider("02", "Hermes-Agent 指南", "对话式AI智能助手 · 生产运维部全员适用");

// Slide: 安装配置概览
let s5 = pres.addSlide();
s5.background = { color: C.white };
s5.addText("Hermes-Agent 安装与配置", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

card(s5, 0.6, 1.2, 2.7, 2.0, "🐍", "环境准备", "公司应用商店搜索安装 Python\n版本要求：3.11及以上\n勾选 Add Python to PATH", C.blue);
card(s5, 3.6, 1.2, 2.7, 2.0, "📦", "一键安装", "打开终端复制安装脚本\nCMD 或 PowerShell 均可\n自动配置 pip 内部源", C.green);
card(s5, 6.6, 1.2, 2.7, 2.0, "⚙️", "配置模型", "执行 hermes setup\n填入 Base URL + API Key\n模型名：Qwen3.6-35B-A3B", C.orange);

// CMD code block
s5.addText("CMD 安装脚本", { x: 0.6, y: 3.5, w: 4, h: 0.3, fontSize: 11, fontFace: "Arial Black", color: C.dkText, margin: 0 });
codeBlock(s5, 0.6, 3.8, 4.2, 1.6,
`@echo off
echo ========================================
echo   Hermes-Agent 一键安装脚本 (CMD)
echo ========================================
echo [1/2] 配置 pip 内部源...
pip config set global.index-url http://7.24.4.68:28081/repository/pypi/simple/
pip config set global.trusted-host 7.24.4.68
echo [2/2] 安装 hermes-agent...
pip install -U hermes-agent[all]
echo 安装完成！输入 hermes-agent --help 验证
pause`);

// Tips on the right
tipBox(s5, 5.2, 3.5, 4.2, "脚本自动配置pip使用公司内部源，无需手动修改pip.conf", "info");
tipBox(s5, 5.2, 4.2, 4.2, "安装Python时务必勾选「Add Python to PATH」", "warn");
tipBox(s5, 5.2, 4.9, 4.2, "推荐模型：Qwen3.6-35B-A3B（日常办公聊天场景）", "info");
addSlideNum(s5, 5);

// Slide: Skills + 使用
let s6 = pres.addSlide();
s6.background = { color: C.offWht };
s6.addText("Skills 技能系统 & 使用建议", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

// 2x2 card grid
const skillsData = [
  ["📝", "文档处理", "Word/PDF/Excel 读写与分析，自动化办公文档生成"],
  ["💻", "代码开发", "TDD调试、Code Review、架构设计、技术方案"],
  ["🎨", "创意设计", "ASCII艺术、架构图绘制、品牌指南、漫画生成"],
  ["📊", "数据分析", "数据可视化、统计报告、趋势分析、看板生成"],
];
skillsData.forEach((item, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  card(s6, 0.6 + col * 4.5, 1.2 + row * 1.5, 4.2, 1.3, item[0], item[1], item[2], [C.blue, C.green, C.purple, C.orange][i]);
});

// Usage tips
s6.addText("提示词技巧", { x: 0.6, y: 4.35, w: 3, h: 0.3, fontSize: 14, fontFace: "Arial Black", color: C.dkText, margin: 0 });
s6.addText([
  { text: "① 角色设定：设定具体角色提升专业性", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: "Calibri", color: C.gray } },
  { text: "② 结构化指令：背景→任务→要求→输出格式", options: { bullet: true, breakLine: true, fontSize: 10, fontFace: "Calibri", color: C.gray } },
  { text: "③ 多轮迭代：AI生成→观察→追问→调整", options: { bullet: true, fontSize: 10, fontFace: "Calibri", color: C.gray } },
], { x: 0.6, y: 4.7, w: 8.5, h: 0.8, margin: 0 });
addSlideNum(s6, 6);

// ═══════════════════════════════════════════
// CH3: Claude Code
// ═══════════════════════════════════════════
sectionDivider("03", "Claude Code 指南", "终端AI编程协作工具 · 面向开发工程师");

// Slide: Claude Code 安装
let s7 = pres.addSlide();
s7.background = { color: C.white };
s7.addText("Claude Code 安装流程", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

// 3 step cards
const ccSteps = [
  { icon: "🟢", title: "安装 Node.js", desc: "下载 node-v24.16.0-win-x64.zip\n解压并配置 PATH 环境变量\n验证：node --version", color: C.green },
  { icon: "📦", title: "安装 Claude Code", desc: "配置 npm 内部源\nnpm install -g @anthropic-ai/claude-code\n创建 .claude 配置目录", color: C.blue },
  { icon: "⚙️", title: "配置 & 启动", desc: "编辑 settings.json\n填入 API Key + Base URL\n运行 claude 命令启动", color: C.purple },
];
ccSteps.forEach((s, i) => {
  card(s7, 0.6 + i * 3.1, 1.2, 2.9, 1.7, s.icon, s.title, s.desc, s.color);
});

// Code blocks side by side
codeBlock(s7, 0.6, 3.2, 4.2, 1.8,
`@echo off
echo ========================================
echo   Claude Code 一键安装脚本
echo ========================================
echo [1/3] 检查 Node.js 环境...
where node >nul 2>&1 || (echo [错误] && goto :end)
node --version && npm --version
echo [2/3] 配置 npm 源并安装 Claude Code...
npm config set registry http://7.24.4.68:28081/repository/npm/
npm install -g @anthropic-ai/claude-code@2.1.153
echo [3/3] 创建配置目录...
if not exist "%USERPROFILE%\\.claude" mkdir "%USERPROFILE%\\.claude"
echo 安装完成！运行 claude --version 验证
:end
pause`);

// Config JSON
s7.addText("settings.json 配置模板", { x: 5.2, y: 3.2, w: 4, h: 0.3, fontSize: 11, fontFace: "Arial Black", color: C.dkText, margin: 0 });
codeBlock(s7, 5.2, 3.5, 4.2, 0.65,
`{
  "ANTHROPIC_API_KEY": "你的API_KEY",
  "ANTHROPIC_BASE_URL": "http://7.24.28.9:8080"
}`);

// Command table
s7.addText("常用命令", { x: 5.2, y: 4.3, w: 3, h: 0.3, fontSize: 11, fontFace: "Arial Black", color: C.dkText, margin: 0 });
const cmdData = [
  [{ text: "命令", options: { bold: true, color: C.white, fill: { color: C.purple }, fontSize: 8, fontFace: "Arial Black" } },
   { text: "说明", options: { bold: true, color: C.white, fill: { color: C.purple }, fontSize: 8, fontFace: "Arial Black" } }],
  ["claude", "启动交互会话"],
  ["claude --resume", "恢复上次会话"],
  ["/compact", "压缩上下文"],
  ["/review", "审查代码变更"],
  ["/init", "初始化 CLAUDE.md"],
].map((r, ri) => r.map((c, ci) => {
  if (typeof c === "string") return { text: c, options: { fontSize: 8, fontFace: "Consolas", color: C.dkText, fill: { color: ri%2===0 ? C.white : C.offWht } } };
  return { text: c.text, options: { ...{ fontSize: 8, fontFace: "Calibri", color: C.dkText }, ...c.options } };
}));
s7.addTable(cmdData, { x: 5.2, y: 4.6, w: 4.2, colW: [2.0, 2.2], rowH: [0.28, 0.28, 0.28, 0.28, 0.28, 0.28], border: { pt: 0.5, color: C.ltGray } });
addSlideNum(s7, 7);

// ═══════════════════════════════════════════
// CH4: 大模型基础
// ═══════════════════════════════════════════
sectionDivider("04", "大模型基础知识", "LLM基础 · Prompt工程 · 模型接入配置 · Function Call · MCP · Agent");

// Slide: LLM + Prompt
let s8 = pres.addSlide();
s8.background = { color: C.offWht };
s8.addText("大语言模型 & 提示词工程", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

// LLM core concepts - 3 cards
card(s8, 0.6, 1.1, 2.7, 1.5, "🔤", "Token（词元）", "模型处理文本的最小单位\n中文≈1.5字符=1 token\nAPI调用成本与容量基础单位", C.blue);
card(s8, 3.6, 1.1, 2.7, 1.5, "📐", "上下文窗口", "模型的短期记忆容量\n超出窗口需开新对话\n或使用摘要压缩", C.green);
card(s8, 6.6, 1.1, 2.7, 1.5, "🌡️", "Temperature", "控制输出随机性\n0~0.3：精确、一致\n0.7~1.0：创意、多样", C.orange);

// Prompt techniques
s8.addText("提示词工程 — 从基础到进阶", { x: 0.6, y: 2.9, w: 8, h: 0.4, fontSize: 16, fontFace: "Arial Black", color: C.dkText, margin: 0 });
const promptTech = [
  ["🎭", "角色设定", "开头设定角色提升专业性", C.blue],
  ["📋", "结构化指令", "背景→任务→要求→输出格式", C.green],
  ["📝", "Few-shot", "给出2~3组示例引导格式", C.purple],
  ["🧠", "思维链 CoT", "引导逐步推理，加\"让我们一步步思考\"", C.orange],
  ["📊", "结构化输出", "指定JSON/表格等输出格式", C.cyan],
];
promptTech.forEach((t, i) => {
  card(s8, 0.6 + i * 1.8, 3.4, 1.65, 1.3, t[0], t[1], t[2], t[3]);
});

// Model comparison table
s8.addText("主流大模型一览", { x: 0.6, y: 4.85, w: 4, h: 0.3, fontSize: 12, fontFace: "Arial Black", color: C.dkText, margin: 0 });
const modelData = [
  [{ text: "模型", options: { bold: true, color: C.white, fill: { color: C.blue }, fontSize: 8, fontFace: "Arial Black" } },
   { text: "公司", options: { bold: true, color: C.white, fill: { color: C.blue }, fontSize: 8, fontFace: "Arial Black" } },
   { text: "特点", options: { bold: true, color: C.white, fill: { color: C.blue }, fontSize: 8, fontFace: "Arial Black" } }],
  ["GPT-4o", "OpenAI", "多模态，生态成熟"],
  ["Claude 4", "Anthropic", "安全性高，推理严谨"],
  ["DeepSeek", "深度求索", "国产开源，性价比极高"],
  ["GLM", "智谱AI", "国产自研，中文深入"],
  ["Qwen", "阿里云", "开源丰富，部署成熟"],
].map((r, ri) => r.map((c, ci) => {
  if (typeof c === "string") return { text: c, options: { fontSize: 8, fontFace: "Calibri", color: C.dkText, fill: { color: ri%2===0 ? C.white : C.offWht } } };
  return { text: c.text, options: { ...{ fontSize: 8, fontFace: "Calibri", color: C.dkText }, ...c.options } };
}));
s8.addTable(modelData, { x: 0.6, y: 5.1, w: 5.5, colW: [1.3, 1.1, 3.1], border: { pt: 0.5, color: C.ltGray } });
addSlideNum(s8, 8);

// Slide: API Config + Function Call + MCP
let s9 = pres.addSlide();
s9.background = { color: C.white };
s9.addText("模型接入配置 & 核心协议", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

// Config concepts
s9.addText("接入配置三要素", { x: 0.6, y: 1.1, w: 4, h: 0.3, fontSize: 14, fontFace: "Arial Black", color: C.dkText, margin: 0 });
[
  ["🏠", "Base URL", "AI服务的门牌号\nhttp://7.24.28.9:28080/v1"],
  ["🔑", "API Key", "身份通行证\n从AI Gateway平台申请"],
  ["🧠", "Model Name", "指定使用的大脑\nQwen3.6-35B-A3B"],
].forEach((item, i) => {
  card(s9, 0.6 + i * 3.1, 1.5, 2.9, 1.15, item[0], item[1], item[2], C.blue);
});

// Function Call
s9.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 2.9, w: 4.2, h: 2.5, fill: { color: C.ice } });
s9.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 2.9, w: 0.06, h: 2.5, fill: { color: C.blue } });
s9.addText("📞 Function Call", { x: 0.85, y: 3.0, w: 3.5, h: 0.4, fontSize: 14, fontFace: "Arial Black", color: C.dkText, margin: 0 });
s9.addText("让大模型从\"会说\"到\"会做\"", { x: 0.85, y: 3.4, w: 3.5, h: 0.25, fontSize: 10, fontFace: "Calibri", color: C.gray, italic: true, margin: 0 });
s9.addText([
  { text: "模型不自己调接口，输出JSON调用指令", options: { bullet: true, breakLine: true, fontSize: 9.5, fontFace: "Calibri", color: C.gray } },
  { text: "程序执行函数 → 结果返回模型", options: { bullet: true, breakLine: true, fontSize: 9.5, fontFace: "Calibri", color: C.gray } },
  { text: "六步流程：请求→判断→JSON→执行→返回→回复", options: { bullet: true, breakLine: true, fontSize: 9.5, fontFace: "Calibri", color: C.gray } },
  { text: "模型是大脑，Function Call是手", options: { bullet: true, fontSize: 9.5, fontFace: "Calibri", color: C.blue, bold: true } },
], { x: 0.85, y: 3.7, w: 3.7, h: 1.5, margin: 0 });

// MCP
s9.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.9, w: 4.2, h: 2.5, fill: { color: C.ice } });
s9.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.9, w: 0.06, h: 2.5, fill: { color: C.green } });
s9.addText("🔌 MCP 协议", { x: 5.45, y: 3.0, w: 3.5, h: 0.4, fontSize: 14, fontFace: "Arial Black", color: C.dkText, margin: 0 });
s9.addText("AI应用的\"USB-C接口标准\"", { x: 5.45, y: 3.4, w: 3.5, h: 0.25, fontSize: 10, fontFace: "Calibri", color: C.gray, italic: true, margin: 0 });
s9.addText([
  { text: "Client（AI端）↔ 标准协议 ↔ Server（工具端）", options: { bullet: true, breakLine: true, fontSize: 9.5, fontFace: "Calibri", color: C.gray } },
  { text: "Server暴露3种能力：Tools/Resources/Prompts", options: { bullet: true, breakLine: true, fontSize: 9.5, fontFace: "Calibri", color: C.gray } },
  { text: "传输：stdio（本地）+ HTTP/SSE（远程）", options: { bullet: true, breakLine: true, fontSize: 9.5, fontFace: "Calibri", color: C.gray } },
  { text: "Claude Code & Hermes-Agent 均已深度集成", options: { bullet: true, fontSize: 9.5, fontFace: "Calibri", color: C.green, bold: true } },
], { x: 5.45, y: 3.7, w: 3.7, h: 1.5, margin: 0 });

addSlideNum(s9, 9);

// Slide: Agent + Evolution chain
let s10 = pres.addSlide();
s10.background = { color: C.offWht };
s10.addText("AI Agent & 工程化演进", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

// Agent formula
s10.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.1, w: 8.8, h: 0.8, fill: { color: C.navy } });
s10.addText("Agent = 大模型(大脑) + 工具调用(手) + 记忆系统(笔记本) + 规划能力(计划表) + 验证机制(质检员)",
  { x: 0.6, y: 1.1, w: 8.8, h: 0.8, fontSize: 13, fontFace: "Arial Black", color: C.white, align: "center", margin: 0 });

// Agent loop
s10.addText("核心循环", { x: 0.6, y: 2.15, w: 2, h: 0.3, fontSize: 13, fontFace: "Arial Black", color: C.dkText, margin: 0 });
const loopSteps = ["感知", "思考", "规划", "行动", "观察", "迭代"];
loopSteps.forEach((step, i) => {
  const x = 0.6 + i * 1.5;
  s10.addShape(pres.shapes.OVAL, { x, y: 2.55, w: 0.9, h: 0.9, fill: { color: i===0||i===3 ? C.blue : C.ice } });
  s10.addText(step, { x, y: 2.55, w: 0.9, h: 0.9, fontSize: 12, fontFace: "Arial Black", color: i===0||i===3 ? C.white : C.dkText, align: "center", margin: 0 });
  if (i < 5) s10.addText("→", { x: x+0.9, y: 2.5, w: 0.6, h: 0.9, fontSize: 20, fontFace: "Calibri", color: C.gray, align: "center", margin: 0 });
});

// Evolution chain
s10.addText("工程化演进：Prompt → Context → Harness → Loop", { x: 0.6, y: 3.7, w: 8, h: 0.4, fontSize: 16, fontFace: "Arial Black", color: C.dkText, margin: 0 });

const evoData = [
  [{ text: "阶段", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: "Arial Black" } },
   { text: "时间", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: "Arial Black" } },
   { text: "核心问题", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: "Arial Black" } },
   { text: "关键能力", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: "Arial Black" } },
   { text: "人的角色", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: "Arial Black" } }],
  ["Prompt Eng.", "2023", "怎么把话说清楚？", "角色设定、思维链、Few-shot", "提问者"],
  ["Context Eng.", "2024-25", "Agent应该知道什么？", "RAG、记忆系统、MCP协议", "信息管家"],
  ["Harness Eng.", "2025", "Agent在什么环境做事？", "约束门、反馈回路、沙箱", "规则制定者"],
  ["Loop Eng.", "2026", "怎么让系统自动管Agent？", "自动化触发、Sub-agent", "循环设计者"],
].map((r, ri) => r.map((c, ci) => {
  if (typeof c === "string") return { text: c, options: { fontSize: 9, fontFace: "Calibri", color: C.dkText, fill: { color: ri%2===0 ? C.white : C.offWht } } };
  return { text: c.text, options: { ...{ fontSize: 9, fontFace: "Calibri", color: C.dkText }, ...c.options } };
}));
s10.addTable(evoData, { x: 0.6, y: 4.2, w: 8.8, colW: [1.5, 0.9, 2.4, 2.4, 1.6], border: { pt: 0.5, color: C.ltGray } });
addSlideNum(s10, 10);

// ═══════════════════════════════════════════
// CH5: API Key
// ═══════════════════════════════════════════
sectionDivider("05", "API Key 申请指南", "从申请到配置 · 5分钟完成 · 康龙雨审批");

// Slide: API Key flow
let s11 = pres.addSlide();
s11.background = { color: C.white };
s11.addText("API Key 申请流程", { x: 0.6, y: 0.3, w: 8, h: 0.6, fontSize: 26, fontFace: "Arial Black", color: C.dkText, bold: true, margin: 0 });

const flowSteps = [
  ["1", "访问平台", "访问 aigateway.sccba.org\n域账号登录", C.blue],
  ["2", "令牌管理", "点击「令牌管理」\n查看或申请令牌", C.cyan],
  ["3", "填写申请", "选择个人使用类型\n填写名称和描述", C.green],
  ["4", "等待审批", "提交后联系康龙雨\n联盟E动审批", C.orange],
  ["5", "复制保存", "复制令牌字符串\n妥善保存勿泄露", C.purple],
];
flowSteps.forEach((step, i) => {
  const x = 0.4 + i * 1.9;
  card(s11, x, 1.2, 1.7, 1.8, "0"+step[0], step[1], step[2], step[3]);
  if (i < 4) s11.addText("→", { x: x+1.7, y: 1.8, w: 0.3, h: 0.5, fontSize: 22, fontFace: "Arial Black", color: C.gray, align: "center", margin: 0 });
});

// Key management
s11.addText("API Key 管理要点", { x: 0.6, y: 3.3, w: 4, h: 0.4, fontSize: 16, fontFace: "Arial Black", color: C.dkText, margin: 0 });
[
  ["👁️", "查看列表", "管理页面查看\n所有Key及状态"],
  ["🔄", "重新生成", "Key丢失可重新生成\n旧Key立即失效"],
  ["🔒", "吊销", "Key泄露立即吊销\n长期有效无需续期"],
  ["⚠️", "安全提醒", "勿截图泄露、明文传输\n勿提交代码仓库"],
].forEach((item, i) => {
  card(s11, 0.6 + i * 2.35, 3.7, 2.15, 1.2, item[0], item[1], item[2], i===3 ? C.red : C.blue);
});

// FAQ
s11.addText("常见问题", { x: 0.6, y: 5.05, w: 3, h: 0.3, fontSize: 11, fontFace: "Arial Black", color: C.dkText, margin: 0 });
s11.addText([
  { text: "Q: 一个Key可用于多个工具？  A: 可以，无限制", options: { fontSize: 8.5, fontFace: "Calibri", color: C.gray, breakLine: true } },
  { text: "Q: Key有使用限制？  A: 每分钟最多8次请求", options: { fontSize: 8.5, fontFace: "Calibri", color: C.gray, breakLine: true } },
  { text: "Q: Key会过期吗？  A: 不会，长期有效", options: { fontSize: 8.5, fontFace: "Calibri", color: C.gray, breakLine: true } },
  { text: "Q: 需要审批吗？  A: 需要，联系康龙雨（联盟E动）审批", options: { fontSize: 8.5, fontFace: "Calibri", color: C.orange, bold: true } },
], { x: 0.6, y: 5.3, w: 8.5, h: 0.5, margin: 0 });
addSlideNum(s11, 11);

// ═══════════════════════════════════════════
// SLIDE 12: ENDING
// ═══════════════════════════════════════════
let s12 = pres.addSlide();
s12.background = { color: C.navy };
s12.addShape(pres.shapes.OVAL, { x: -2, y: -2, w: 6, h: 6, fill: { color: C.dkBlue, transparency: 40 } });
s12.addShape(pres.shapes.OVAL, { x: 7, y: 3, w: 5, h: 5, fill: { color: C.dkBlue, transparency: 50 } });
s12.addText("开始你的 AI 之旅", { x: 1, y: 1.5, w: 8, h: 1, fontSize: 42, fontFace: "Arial Black", color: C.white, bold: true, align: "center", margin: 0 });
s12.addShape(pres.shapes.RECTANGLE, { x: 4.0, y: 2.6, w: 2, h: 0.05, fill: { color: C.blue } });
s12.addText("如有疑问，请联系技术支持：李龙(lilong) · 司佳宇(sijy)", { x: 1, y: 3.0, w: 8, h: 0.5, fontSize: 13, fontFace: "Calibri", color: C.gray, align: "center", margin: 0 });
s12.addText("生产运维部 · 内部培训资料 · 2026年6月", { x: 1, y: 3.5, w: 8, h: 0.4, fontSize: 11, fontFace: "Calibri", color: C.gray, align: "center", margin: 0 });

// ── Write ──
const outFile = "AI赋能日常工作_培训PPT.pptx";
pres.writeFile({ fileName: outFile }).then(() => {
  console.log("PPT created: " + outFile);
}).catch(err => {
  console.error("Error:", err);
});
