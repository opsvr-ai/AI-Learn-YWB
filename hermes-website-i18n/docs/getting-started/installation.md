---
sidebar_position: 0
title: "安装指南"
description: "Hermes Agent 安装指南 — 支持 Linux、macOS、WSL2 和 Windows"
---

# 安装指南

## 支持平台

| 平台 | 状态 | 安装方式 |
|------|------|----------|
| Linux | 完全支持 | curl 脚本 |
| macOS | 完全支持 | curl 脚本 |
| WSL2 | 完全支持 | curl 脚本 |
| Windows 原生 | 早期测试版 | PowerShell 脚本 |
| Android (Termux) | 支持 | curl 脚本 |

## 快速安装

### Linux / macOS / WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows (PowerShell)

以管理员身份运行 PowerShell：

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

### Android (Termux)

与 Linux 使用相同的 curl 命令，安装器会自动检测 Termux 环境。

## 安装器做了什么

安装脚本会：

1. 检测操作系统和架构
2. 下载最新的 Hermes Agent 二进制文件
3. 安装到 `~/.hermes/bin/`（用户级）或 `/usr/local/bin/`（系统级）
4. 将安装路径添加到 PATH
5. 创建默认配置目录 `~/.hermes/`

## 验证安装

```bash
hermes --version
```

如果输出版本号，说明安装成功。

## 更新

```bash
hermes update
```

或重新运行安装脚本，会自动覆盖旧版本。

## 卸载

```bash
# 删除二进制和配置
rm -rf ~/.hermes
```

## 常见安装问题

### 权限被拒绝

```bash
# 如果是权限问题，使用 sudo
sudo bash install.sh
```

### 找不到命令

重启终端或手动将 `~/.hermes/bin` 添加到 PATH：

```bash
export PATH="$HOME/.hermes/bin:$PATH"
```

### Windows 安全警告

Windows 可能拦截安装脚本。请在「Windows 安全中心」中允许运行，或暂时关闭实时保护。
