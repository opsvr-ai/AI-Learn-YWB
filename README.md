# AI 赋能日常工作

生产运维部内部 AI 培训站点，涵盖 Hermes-Agent、Claude Code 等 AI 工具的使用教程、案例分享与问题反馈。

纯静态 HTML 站点，浏览器直接打开即可使用，无需服务器环境。

## 技术栈

HTML5 + CSS3 + 原生 JavaScript，零框架依赖。浅色主题，蓝色系主色调，现代简约卡片式布局。桌面端优先。

## 页面

| 文件 | 内容 |
| --- | --- |
| index.html | 首页 |
| hermes.html | Hermes-Agent 教程 |
| claude.html | Claude Code 教程 |
| ai-basics.html | 大模型基础知识 |
| api-key.html | API Key 申请 |
| token-stats.html | Token 消耗统计 |
| cases.html | 案例分享 |
| feedback.html | 问题反馈 |
| hermes-docs/ | Hermes 官方文档 |

## 快速开始

方式一：浏览器直接打开 .html 文件

方式二：启动本地 HTTP 服务（支持视频拖拽、打卡 API）

python server.py

默认运行在 http://0.0.0.0:8080

## 目录

核心文件：css/style.css、js/main.js、js/cases-upload.js

资源：images/ 截图、tutorials/ PDF教程、videos/ 视频、uploads/ 用户上传

工具：server.py 本地服务、translate_docs.py 翻译脚本

已忽略：packages/ 安装包、素材/ 原始素材、.visit_stats.db 数据库

## API

server.py 提供统计上报、打卡、案例/反馈管理、图片上传等接口。

## 维护

导航栏在各 HTML 中重复，修改需同步所有主页面及 hermes-docs/。templates/nav.html 为模板源。

内网 AI Gateway IP 变更时需同步修改 api-key.html、hermes.html、claude.html 等文件的地址。

---

Copyright 生产运维部，内部学习资料
