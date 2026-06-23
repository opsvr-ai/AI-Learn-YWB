#!/usr/bin/env python3
"""Generate the comprehensive AI learning PDF."""
import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register CJK Fonts ──
pdfmetrics.registerFont(TTFont('MSYH', 'C:/Windows/Fonts/msyh.ttc', subfontIndex=0))
FONT = 'MSYH'

# ── Colors ──
C_PRIMARY   = HexColor('#2563eb')
C_DARK      = HexColor('#1e293b')
C_GRAY      = HexColor('#64748b')
C_WHITE     = white
C_BLACK     = HexColor('#0f172a')
C_CODE_BG   = HexColor('#1e293b')
C_BLUE_BG   = HexColor('#eff6ff')
C_AMBER_BG  = HexColor('#fef3c7')
C_LIGHT_BG  = HexColor('#f8fafc')
C_BORDER    = HexColor('#cbd5e1')

PAGE_W, PAGE_H = A4

# ── Styles ──
style_body = ParagraphStyle('body', fontName=FONT, fontSize=10, leading=18,
    textColor=C_BLACK, alignment=TA_JUSTIFY, spaceAfter=8)
style_h1 = ParagraphStyle('h1', fontName=FONT, fontSize=22, leading=32,
    textColor=C_PRIMARY, spaceAfter=14, spaceBefore=20)
style_h2 = ParagraphStyle('h2', fontName=FONT, fontSize=15, leading=24,
    textColor=C_DARK, spaceAfter=10, spaceBefore=16)
style_h3 = ParagraphStyle('h3', fontName=FONT, fontSize=12, leading=20,
    textColor=C_DARK, spaceAfter=8, spaceBefore=12)
style_h4 = ParagraphStyle('h4', fontName=FONT, fontSize=10.5, leading=18,
    textColor=C_DARK, spaceAfter=6, spaceBefore=10)
style_code = ParagraphStyle('code', fontName='Courier', fontSize=7.5, leading=11,
    textColor=HexColor('#e2e8f0'), backColor=C_CODE_BG, borderPadding=10,
    spaceAfter=12, spaceBefore=8, fontNameInner='Courier')
style_tip = ParagraphStyle('tip', fontName=FONT, fontSize=9, leading=15,
    textColor=C_DARK, backColor=C_BLUE_BG, borderPadding=10,
    spaceAfter=10, spaceBefore=6)
style_warn = ParagraphStyle('warn', fontName=FONT, fontSize=9, leading=15,
    textColor=HexColor('#92400e'), backColor=C_AMBER_BG, borderPadding=10,
    spaceAfter=10, spaceBefore=6)
style_cover_title = ParagraphStyle('ctitle', fontName=FONT, fontSize=32, leading=44,
    textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=10)
style_cover_sub = ParagraphStyle('csub', fontName=FONT, fontSize=13, leading=22,
    textColor=HexColor('#94a3b8'), alignment=TA_CENTER, spaceAfter=6)
style_toc = ParagraphStyle('toc', fontName=FONT, fontSize=11.5, leading=30,
    textColor=C_DARK, leftIndent=16)

# ── Helpers ──
def h1(t):  return Paragraph(t, style_h1)
def h2(t):  return Paragraph(t, style_h2)
def h3(t):  return Paragraph(t, style_h3)
def h4(t):  return Paragraph(t, style_h4)
def body(t): return Paragraph(t, style_body)
def sp(h=10): return Spacer(1, h)
def tip(t): return Paragraph(f'<b>[提示]</b>  {t}', style_tip)
def warn(t): return Paragraph(f'<b>[注意]</b>  {t}', style_warn)

def code_block(text):
    lines = text.strip().split('\n')
    escaped = []
    for line in lines:
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped.append(line)
    return Paragraph('<br/>'.join(escaped), style_code)

def make_table(headers, rows, col_widths=None):
    if col_widths is None:
        avail = PAGE_W - 50*mm
        col_widths = [avail / len(headers)] * len(headers)
    all_data = [headers] + rows
    t = Table(all_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), C_WHITE),
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_WHITE, C_LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t

def hr():
    from reportlab.platypus import HRFlowable
    return HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=10, spaceBefore=6)

# ── Page number canvas ──
from reportlab.pdfgen import canvas as rl_canvas
class NumberedCanvas:
    def __init__(self, *args, **kwargs):
        self._saved_page_states = []
        self.canv = rl_canvas.Canvas(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(self.canv, name)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(25*mm, PAGE_H - 18*mm, PAGE_W - 25*mm, PAGE_H - 18*mm)
    canvas.setFont(FONT, 7)
    canvas.setFillColor(C_GRAY)
    canvas.drawString(25*mm, PAGE_H - 16*mm, "AI赋能日常工作 - 学习资料")
    canvas.drawRightString(PAGE_W - 25*mm, PAGE_H - 16*mm, f"第 {doc.page} 页")
    canvas.line(25*mm, 17*mm, PAGE_W - 25*mm, 17*mm)
    canvas.drawString(25*mm, 14*mm, "生产运维部 - 内部学习资料")
    canvas.restoreState()

def on_cover(canvas, doc): pass

# ── Build PDF ──
def build_pdf():
    output = "AI赋能日常工作_学习资料.pdf"
    doc = BaseDocTemplate(output, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm,
        topMargin=25*mm, bottomMargin=25*mm,
        title='AI赋能日常工作 学习资料', author='生产运维部')

    frame_cover = Frame(0, 0, PAGE_W, PAGE_H, id='cover')
    frame_normal = Frame(25*mm, 25*mm, PAGE_W-50*mm, PAGE_H-50*mm, id='normal')

    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[frame_cover], onPage=on_cover),
        PageTemplate(id='Normal', frames=[frame_normal], onPage=on_page),
    ])

    S = []

    # ═════════ COVER ═════════
    S.append(Spacer(1, PAGE_H/2 - 100))
    S.append(Paragraph("AI赋能日常工作", style_cover_title))
    S.append(sp(8))
    S.append(Paragraph("人工智能工具学习手册", style_cover_sub))
    S.append(sp(16))
    S.append(Paragraph("涵盖 Hermes-Agent / Claude Code / 大模型基础 / API Key 申请", style_cover_sub))
    S.append(sp(36))
    S.append(Paragraph("生产运维部 - 内部学习资料", ParagraphStyle('d1', fontName=FONT, fontSize=11, textColor=C_GRAY, alignment=TA_CENTER)))
    S.append(Paragraph("2026年6月", ParagraphStyle('d2', fontName=FONT, fontSize=11, textColor=C_GRAY, alignment=TA_CENTER)))
    S.append(PageBreak())

    # ═════════ TOC ═════════
    S.append(h1("目  录"))
    S.append(sp(16))
    toc = [
        ("第一章", "平台概述", "两大工具对比、三步快速开始"),
        ("第二章", "Hermes-Agent 使用指南", "环境准备、安装配置、Skills、使用方法"),
        ("第三章", "Claude Code 使用指南", "Node.js环境、安装配置、常用命令"),
        ("第四章", "大模型基础知识", "LLM基础、Prompt工程、模型配置、Function Call、MCP、Agent"),
        ("第五章", "API Key 申请指南", "申请流程、令牌管理、常见问题"),
        ("附录", "常用链接与资源", "内部平台、下载资源、注意事项"),
    ]
    for ch, title, desc in toc:
        S.append(Paragraph(
            f'<b>{ch}</b>&nbsp;&nbsp;&nbsp;{title}<br/>'
            f'<font size="9" color="#94a3b8">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{desc}</font>',
            style_toc))
        S.append(sp(8))
    S.append(PageBreak())

    # ═════════ CH1: 平台概述 ═════════
    S.append(h1("第一章  平台概述"))
    S.append(body("本学习平台旨在帮助生产运维部全体同事快速掌握AI工具的使用方法，从零基础到熟练应用。"))
    S.append(sp(4))

    S.append(h2("1.1  两大核心工具对比"))
    S.append(make_table(
        ['对比维度', 'Hermes-Agent', 'Claude Code'],
        [
            ['定位', '对话式AI智能助手', '终端AI编程协作工具'],
            ['目标用户', '生产运维部全员', '开发工程师'],
            ['核心能力', '日常办公、文档处理、报告编写', '代码开发、调试、Code Review'],
            ['运行环境', '终端 / TUI / 桌面端', '命令行终端'],
            ['接口类型', 'OpenAI兼容接口', 'Anthropic原生接口'],
            ['推荐模型', 'Qwen3.6-35B-A3B', 'Claude系列'],
            ['学习难度', '低，开箱即用', '中，需基础命令行知识'],
            ['安装前提', 'Python 3.11+', 'Node.js 24+'],
        ],
        [None, 220, 220]
    ))
    S.append(sp(12))

    S.append(h2("1.2  三步快速开始"))
    S.append(body("<b>第一步：申请API Key</b> — 访问AI Gateway平台（http://aigateway.sccba.org/）申请令牌。详见第五章。"))
    S.append(body("<b>第二步：安装工具</b> — 根据角色选择安装Hermes-Agent（全员适用）或Claude Code（开发人员）。详见第二、三章。"))
    S.append(body("<b>第三步：开始使用</b> — 配置API Key后即可开始与AI对话，逐步探索更多功能。"))

    S.append(h2("1.3  使用场景速查"))
    S.append(body("<b>日常办公</b>（写报告、写邮件、文档处理、数据分析）→ 使用 <b>Hermes-Agent</b>"))
    S.append(body("<b>代码开发</b>（编程、调试、Code Review、架构设计）→ 使用 <b>Claude Code</b>"))
    S.append(body("两个工具可同时安装，各取所需，互不冲突。"))
    S.append(PageBreak())

    # ═════════ CH2: Hermes-Agent ═════════
    S.append(h1("第二章  Hermes-Agent 使用指南"))
    S.append(sp(4))

    S.append(h2("2.1  环境准备"))
    S.append(body("Hermes-Agent 需要 <b>Python 3.11 及以上版本</b>。首先通过公司应用商店（http://7.24.4.123/Matrix/）搜索并安装 Python，安装时勾选「Add Python to PATH」选项。"))

    S.append(h3("一键安装脚本（CMD）"))
    S.append(code_block("""@echo off
echo ========================================
echo   Hermes-Agent 一键安装脚本 (CMD)
echo ========================================
echo.
echo [1/2] 配置 pip 内部源...
pip config set global.index-url http://7.24.4.68:28081/repository/pypi/simple/
pip config set global.trusted-host 7.24.4.68
echo [2/2] 安装 hermes-agent...
pip install -U hermes-agent[all]
echo.
echo ========================================
echo   安装完成！输入 hermes-agent --help 验证
echo ========================================
pause"""))

    S.append(h3("一键安装脚本（PowerShell）"))
    S.append(code_block("""Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hermes-Agent 一键安装脚本 (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1/2] 配置 pip 内部源..." -ForegroundColor Yellow
pip config set global.index-url http://7.24.4.68:28081/repository/pypi/simple/
pip config set global.trusted-host 7.24.4.68
Write-Host "[2/2] 安装 hermes-agent..." -ForegroundColor Yellow
pip install -U hermes-agent[all]
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  安装完成！输入 hermes-agent --help 验证" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green"""))

    S.append(tip("脚本会自动配置pip使用公司内部源，无需手动修改pip.conf。"))

    S.append(h2("2.2  安装官方 Skills"))
    S.append(body("Skills 是 Hermes-Agent 的核心能力扩展，提供文档处理、代码开发、创意设计等各领域的专业技能。"))
    S.append(body("<b>步骤：</b>① 首次运行 hermes-agent 命令，系统自动生成 .hermes 配置目录 → ② 下载培训包中的 skills.zip 并解压 → ③ 将解压后的 skills 文件夹内容覆盖到用户目录下的 .hermes/skills/ 目录 → ④ 重启生效。"))

    S.append(h2("2.3  配置模型"))
    S.append(body("安装完成后，需要通过 <b>hermes setup</b> 命令配置模型信息。请提前准备好以下三样信息："))
    S.append(body("<b>① API Key</b> — 从 AI Gateway 平台申请的密钥（详见第五章）。"))
    S.append(body("<b>② Base URL</b> — AI 服务的接口地址，格式如 http://7.24.28.9:28080/v1（以实际分配地址为准）。"))
    S.append(body("<b>③ Model Name</b> — 日常办公聊天推荐使用 <b>Qwen3.6-35B-A3B</b>。"))
    S.append(sp(4))
    S.append(body("配置步骤：终端中执行 <b>hermes setup</b> → 选择自定义端点选项（不要选默认选项1）→ 选择 Custom Endpoint → 依次填入 Base URL、API Key、Model Name。"))
    S.append(tip("不要选择默认的选项1（Quick Setup - Nous Portal OAuth），请选择自定义端点选项。"))

    S.append(h2("2.4  Hermes Desktop 桌面端安装（可选）"))
    S.append(body("Hermes Desktop 仅在 Windows 10/11 上验证通过。安装前请确保已完成上述环境准备和模型配置。"))
    S.append(body("步骤：① 升级 hermes-agent 到完整版（pip install -U hermes-agent[all]）→ ② 安装 WebView2 运行时 → ③ 下载解压 hermes-desktop.zip → ④ 覆盖 config.yaml 到桌面端目录 → ⑤ 启动 Hermes.exe。"))

    S.append(h2("2.5  使用建议"))
    S.append(body("<b>角色设定：</b>在提示词开头设定角色（如“你是一位资深运维工程师”），显著提升输出专业性。"))
    S.append(body("<b>结构化指令：</b>用「背景 → 任务 → 要求 → 输出格式」的结构组织提示词。"))
    S.append(body("<b>多轮迭代：</b>将AI生成内容作为初稿，在此基础上进行追问和调整。"))
    S.append(body("<b>安全提醒：</b>请勿输入公司机密信息和个人敏感数据。"))
    S.append(PageBreak())

    # ═════════ CH3: Claude Code ═════════
    S.append(h1("第三章  Claude Code 使用指南"))
    S.append(sp(4))

    S.append(h2("3.1  环境准备 — 安装 Node.js"))
    S.append(body("Claude Code 依赖 <b>Node.js 24 及以上版本</b>。"))
    S.append(body("1. 下载 Node.js 安装包（packages/node-v24.16.0-win-x64.zip），解压到指定目录。"))
    S.append(body("2. 配置系统环境变量，将 Node.js 路径添加到 PATH 中。"))
    S.append(body("3. 验证安装："))
    S.append(code_block("""node --version
npm --version"""))

    S.append(h2("3.2  安装 Claude Code"))
    S.append(h3("CMD 安装脚本"))
    S.append(code_block("""@echo off
echo ========================================
echo   Claude Code 一键安装脚本
echo ========================================
echo.
echo [1/3] 检查 Node.js 环境...
where node >nul 2>&1 || (echo [错误] 请先安装 Node.js && goto :end)
node --version && npm --version
echo [2/3] 配置 npm 源并安装 Claude Code...
npm config set registry http://7.24.4.68:28081/repository/npm/
npm install -g @anthropic-ai/claude-code@2.1.153
echo [3/3] 创建配置目录...
if not exist "%USERPROFILE%\\.claude" mkdir "%USERPROFILE%\\.claude"
echo.
echo ========================================
echo   安装完成！运行 claude --version 验证
echo ========================================
:end
pause"""))

    S.append(h3("PowerShell 安装脚本"))
    S.append(code_block("""Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Claude Code 一键安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1/3] 检查 Node.js 环境..." -ForegroundColor Yellow
try { node --version; npm --version } catch { Write-Host "[错误] 请先安装 Node.js" -ForegroundColor Red; exit 1 }
Write-Host "[2/3] 配置 npm 源并安装 Claude Code..." -ForegroundColor Yellow
npm config set registry http://7.24.4.68:28081/repository/npm/
npm install -g @anthropic-ai/claude-code@2.1.153
Write-Host "[3/3] 创建配置目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\\.claude" | Out-Null
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  安装完成！运行 claude --version 验证" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green"""))

    S.append(h2("3.3  配置 Claude Code"))
    S.append(body("1. 创建或编辑配置文件 C:\\Users\\你的用户名\\.claude\\settings.json"))
    S.append(body("2. 填入以下配置（将 API_KEY 替换为实际令牌）："))
    S.append(code_block("""{
  "ANTHROPIC_API_KEY": "你的API_KEY",
  "ANTHROPIC_BASE_URL": "http://7.24.28.9:8080"
}"""))
    S.append(body("3. 在终端中运行 <b>claude</b> 命令启动，首次启动可能需要几分钟初始化。"))

    S.append(h2("3.4  常用命令速查"))
    S.append(make_table(
        ['命令', '功能说明'],
        [
            ['claude', '启动 Claude Code 交互会话'],
            ['claude "需求"', '直接以需求描述启动'],
            ['claude --resume', '恢复上一次会话'],
            ['/help', '查看所有可用命令'],
            ['/clear', '清除当前会话上下文'],
            ['/compact', '压缩当前会话上下文'],
            ['/review', '审查最近代码变更'],
            ['/init', '初始化项目 CLAUDE.md 文件'],
        ],
        [160, 330]
    ))
    S.append(PageBreak())

    # ═════════ CH4: 大模型基础 ═════════
    S.append(h1("第四章  大模型基础知识"))
    S.append(sp(4))

    S.append(h2("4.1  大语言模型（LLM）基础"))
    S.append(body("大语言模型（Large Language Model, LLM）是一种基于深度学习的AI模型，通过在数以万亿计的文本数据上进行训练，学习人类语言的模式、结构、知识和推理方式。"))

    S.append(h3("核心概念"))
    S.append(body("<b>Token（词元）：</b>模型处理文本的最小单位。中文约1.5个字符=1个token，英文约0.75个单词=1个token。Token数量决定了API调用成本和上下文容量上限。"))
    S.append(body("<b>上下文窗口（Context Window）：</b>模型的“短期记忆容量”——一次对话中能“看到”的最大文本量。超出窗口时需要开启新对话或做摘要压缩。"))
    S.append(body("<b>Temperature（温度）：</b>控制输出随机性。低温度(0~0.3)让回答更精确一致，适合写代码和查事实；高温度(0.7~1.0)让回答更有创意，适合头脑风暴。"))

    S.append(h3("主流大模型一览"))
    S.append(make_table(
        ['模型', '公司', '特点', '适用场景'],
        [
            ['GPT-4o', 'OpenAI', '多模态，生态成熟', '通用对话、办公自动化'],
            ['Claude 4', 'Anthropic', '安全性高，推理严谨', '编程开发、长文档分析'],
            ['DeepSeek', '深度求索', '国产开源，性价比高', '代码生成、数学推理'],
            ['GLM', '智谱AI', '国产自研，中文深入', '企业级中文应用'],
            ['Qwen（通义千问）', '阿里云', '开源丰富，部署成熟', '电商、办公、中文长文本'],
        ],
        [90, 65, 135, 200]
    ))

    S.append(h2("4.2  提示词工程（Prompt Engineering）"))
    S.append(body("提示词是与大模型沟通的语言。写好提示词，是高效使用AI的第一步。"))
    S.append(body("<b>基础技巧：</b>① <b>角色设定</b>——为模型设定具体角色，显著提升专业性。② <b>结构化指令</b>——用「背景→任务→要求→输出格式」组织。③ <b>Few-shot</b>——给出2~3组示例，让模型理解格式期望。"))
    S.append(body("<b>进阶技巧：</b>④ <b>思维链（Chain-of-Thought）</b>——引导模型逐步推理，加一句“让我们一步一步思考”能大幅提升复杂问题准确率。⑤ <b>结构化输出</b>——明确指定输出格式（JSON、表格等）。"))

    S.append(h2("4.3  模型接入配置基础"))
    S.append(body("<b>Base URL：</b>AI服务的网络地址，如 http://7.24.28.9:28080/v1（协议+IP+端口+版本路径）。"))
    S.append(body("<b>API Key：</b>身份验证凭证。每次请求都带上Key，服务端用它验证身份、控制权限和统计用量。"))
    S.append(body("<b>Model Name：</b>指定使用哪个模型。同一个Base URL下通常有多个模型可选。"))
    S.append(body("<b>接口类型：</b>公司AI Gateway同时支持OpenAI兼容接口（日常办公）和Anthropic原生接口（编码开发）。"))

    S.append(h2("4.4  Function Call（函数调用）"))
    S.append(body("Function Call让大模型不仅会“说”，还会“做”。模型不自己调接口，而是输出调用指令（JSON格式），由程序执行，执行结果再还给模型。<b>模型是大脑，Function Call是手。</b>"))
    S.append(body("六步流程：发送请求+函数列表 → 判断是否需要调用 → 输出调用JSON → 程序执行函数 → 结果返回模型 → 生成最终回复。"))

    S.append(h2("4.5  MCP（模型上下文协议）"))
    S.append(body("MCP是AI应用的“USB-C接口标准”——让任何AI客户端都能无缝对接任何工具和数据源。架构：MCP Client（AI应用端）↔ 标准协议 ↔ MCP Server（工具提供端）。Server暴露三种能力：Tools（调用操作）、Resources（读取数据）、Prompts（提示模板）。"))

    S.append(h2("4.6  AI Agent（智能体）"))
    S.append(body("<b>Agent = 大模型（大脑）+ 工具调用（手）+ 记忆系统（笔记本）+ 规划能力（计划表）+ 验证机制（质检员）</b>"))
    S.append(body("核心循环：感知 → 思考 → 规划 → 行动 → 观察 → 迭代，不断循环直到目标达成。Hermes-Agent 和 Claude Code 本质都是 Agent 产品。"))

    S.append(h2("4.7  工程化进阶：Context → Harness → Loop"))
    S.append(body("AI交互范式经历了四层叠加式递进："))
    S.append(make_table(
        ['阶段', '时间', '核心问题', '关键能力', '人的角色'],
        [
            ['Prompt Engineering', '2023', '怎么把话说清楚？', '角色设定、思维链、Few-shot', '提问者'],
            ['Context Engineering', '2024-25', 'Agent应该知道什么？', 'RAG、记忆系统、MCP协议', '信息管家'],
            ['Harness Engineering', '2025', 'Agent在什么环境中做事？', '约束门、反馈回路、沙箱', '规则制定者'],
            ['Loop Engineering', '2026', '怎么让系统自动管Agent？', '自动化触发、Sub-agent、Worktree', '循环设计者'],
        ],
        [105, 50, 120, 125, 90]
    ))
    S.append(PageBreak())

    # ═════════ CH5: API Key ═════════
    S.append(h1("第五章  API Key 申请指南"))
    S.append(sp(4))
    S.append(body("按照以下步骤在公司内网平台申请API Key，整个过程约5分钟。"))

    S.append(h2("5.1  申请流程"))
    S.append(body("<b>步骤1 — 访问 AI Gateway 平台</b>"))
    S.append(body("使用域账号（OA账号）登录公司内网 AI Gateway：http://aigateway.sccba.org/"))

    S.append(body("<b>步骤2 — 进入令牌管理页面</b>"))
    S.append(body("登录后点击导航栏中的「令牌管理」，查看已有令牌或申请新令牌。"))

    S.append(body("<b>步骤3 — 申请新令牌</b>"))
    S.append(body("点击「申请新令牌」按钮，填写：令牌类型（个人使用）、令牌名称（如“张三-ClaudeCode”）、令牌描述。"))
    S.append(warn("提交令牌申请后，请<b>通过联盟E动联系康龙雨</b>进行审批。审批通过后令牌才会生效，请耐心等待。"))

    S.append(body("<b>步骤4 — 复制并保存令牌</b>"))
    S.append(body("提交申请后系统生成令牌字符串。请<b>立即复制并妥善保存</b>，关闭弹窗后将无法再次查看完整令牌。令牌等同于账号密码，切勿泄露。"))

    S.append(body("<b>步骤5 — 复制 API 接口 URL</b>"))
    S.append(body("平台提供两种兼容接口：Anthropic接口（http://7.24.28.9:8080）和 OpenAI接口（http://7.24.28.9:8080/v1），按需使用。"))

    S.append(body("<b>步骤6 — 选择模型</b>"))
    S.append(body("点击「模型目录」，选择需要的模型。以 anthropic 开头的是兼容 Anthropic 接口的模型。"))

    S.append(body("<b>步骤7 — 配置到工具中使用</b>"))
    S.append(body("Hermes-Agent：在平台设置中填入API Key和接口URL。Claude Code：设置环境变量 ANTHROPIC_API_KEY 和 ANTHROPIC_BASE_URL。"))

    S.append(h2("5.2  API Key 管理"))
    S.append(body("· <b>查看列表</b> — 在管理页面查看所有已申请的Key及其状态。"))
    S.append(body("· <b>重新生成</b> — Key丢失后可重新生成（旧Key立即失效），无需续期。"))
    S.append(body("· <b>吊销</b> — Key泄露或不再使用时应立即吊销/删除。"))

    S.append(h2("5.3  常见问题"))
    S.append(body("<b>Q：一个Key可用于多个工具吗？</b> A：可以，无限制。"))
    S.append(body("<b>Q：有使用限制吗？</b> A：每个Key每分钟最多8次请求。"))
    S.append(body("<b>Q：Key会过期吗？</b> A：不会，长期有效。"))
    S.append(body("<b>Q：忘记保存Key了怎么办？</b> A：回到令牌管理页面重新复制。"))
    S.append(body("<b>Q：需要审批吗？</b> A：需要，提交后通过联盟E动联系康龙雨审批。"))

    S.append(h2("5.4  技术支持"))
    S.append(body("<b>李龙（lilong）</b> — Claude Code、Hermes-Agent 技术支持，API Key 申请与配置协助。"))
    S.append(body("<b>司佳宇（sijy）</b> — AI 工具使用指导、模型相关问题、培训咨询。"))
    S.append(PageBreak())

    # ═════════ APPENDIX ═════════
    S.append(h1("附录  常用链接与资源"))
    S.append(sp(8))

    S.append(h2("内部平台"))
    S.append(body("AI Gateway 平台：http://aigateway.sccba.org/"))
    S.append(body("公司应用商店：http://7.24.4.123/Matrix/"))
    S.append(body("内网 AI 服务（Anthropic）：http://7.24.28.9:8080"))
    S.append(body("内网 AI 服务（OpenAI）：http://7.24.28.9:8080/v1"))
    S.append(sp(8))

    S.append(h2("培训包资源"))
    S.append(body("Python 安装包 → 应用商店搜索安装"))
    S.append(body("Node.js 安装包 → packages/node-v24.16.0-win-x64.zip"))
    S.append(body("Skills 技能包 → packages/skills.zip"))
    S.append(body("Hermes Desktop → packages/hermes-desktop.zip"))
    S.append(body("WebView2 运行时 → packages/MicrosoftEdgeWebView2RuntimeInstallerX64.exe"))
    S.append(body("安装脚本 → packages/install-hermes.ps1 / install-hermes.cmd"))
    S.append(body("配置模板 → packages/settings.json"))
    S.append(body("PDF 教程 → tutorials/ 目录"))
    S.append(sp(8))

    S.append(h2("重要注意事项"))
    S.append(body("1. 所有内网地址均为 HTTP 协议，外网无法访问。"))
    S.append(body("2. API Key 等同于账号密码，切勿截图泄露、不要在即时通讯中明文传输、不要提交到代码仓库。"))
    S.append(body("3. 遇到问题优先查阅本手册相关章节，也可联系技术支持人员：李龙（lilong）、司佳宇（sijy）。"))
    S.append(body("4. 令牌申请审批请联系康龙雨（联盟E动）。"))
    S.append(body("5. 本手册内容如有更新，以培训网站最新版本为准。"))

    # ── Build ──
    doc.build(S, canvasmaker=NumberedCanvas)
    return output

if __name__ == '__main__':
    out = build_pdf()
    print(f"PDF created: {out}")
    # Get page count
    from pypdf import PdfReader
    reader = PdfReader(out)
    print(f"Total pages: {len(reader.pages)}")
