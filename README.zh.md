**Languages**: [🇺🇸 English](README.md) | 🇨🇳 中文

---

# FNS CLI (快速笔记同步命令行工具)

> **从本地到云端**：将 Obsidian 笔记从本地管理转向云端管理和 AI 管理，实现**一次编辑/更新，全端同步**。

FNS CLI 是一个强大的命令行工具，用于与 **[Fast Note Sync (FNS)](https://github.com/haierkeys/fast-note-sync-service)** 服务进行交互。直接在终端中管理、读写和同步你的 Obsidian 笔记 —— 为**人工工作流**和 **AI Agent 集成**而优化。

## 🎯 设计理念

本工具架起了**本地 Obsidian 编辑**与**云端 AI 知识管理**之间的桥梁：

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Obsidian 应用  │────▶│  FNS 服务        │◀────│  FNS CLI (本项目)│
│  (桌面/移动端   │     │  (云端服务器)    │     │  (终端/AI)      │
│   编辑器)       │◀────│                  │────▶│  (读写操作)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  AI Agent            │
                                              │  Claude Code,        │
                                              │  OpenCode, Cursor... │
                                              └─────────────────────┘
```

**一次编辑/更新，全端同步。** 无论你在桌面端 Obsidian 中编辑，还是通过 CLI/AI 在服务器上管理笔记，所有内容都通过 FNS 云端服务保持同步。

## ✨ 功能特性

### 核心功能
- **完整的笔记 CRUD** — 创建、读取、更新、追加、前置、移动、删除
- **智能追加** — 自动处理换行符，防止内容粘连
- **本地文件上传** — 使用 `@file.txt` 前缀上传任意本地文件
- **笔记历史** — 查看和恢复历史版本
- **回收站** — 恢复已删除的笔记
- **查找替换** — 搜索和替换内容（支持正则）
- **跨平台** — macOS / Linux / Windows (Python 3.6+)

### 知识图谱
- **反向链接** — 查看哪些笔记链接到当前笔记
- **出站链接** — 查看当前笔记链接到哪些笔记
- **目录树** — 浏览 Vault 的目录结构

### 文件夹管理
- **创建与删除** — `mkdir`, `folder-delete`
- **浏览** — `folder-list`, `folder-tree`
- **内容列表** — `folder-files`, `folder-notes`
- **元数据** — `folder`

### 文件/附件管理
- **查看与下载** — `file-info`, `file-download [-o 文件]`
- **列表** — `file-list [关键词]`
- **删除与恢复** — `file-delete`, `file-restore`
- **重命名** — `file-rename <旧> <新>`
- **回收** — `file-recycle-clear [路径]`

### 分享与元数据
- **分享链接** — 创建可分享的 URL，支持密码和过期时间
- **Frontmatter 编辑** — 查看和修改笔记元数据（标签、标题等）

### AI Agent 友好
- **`--json` 模式** — 机器可读输出，适合 AI 解析
- **`--quiet` 模式** — 静默操作，适合脚本
- **无交互提示** — 提供参数时完全静默

### 管理功能
- **Vault 管理** — 列表、查看、创建、删除
- **服务器状态** — 检查版本和健康状况
- **自动引导** — 首次登录交互式引导（URL → 凭据 → Vault 选择）

## 📦 安装

### 从 PyPI 安装（推荐）

```bash
pip install fns-cli
```

安装完成后，你就可以在终端直接使用 `fns` 命令。

### 从源码安装

```bash
git clone https://github.com/crazykuma/fns-cli.git
cd fns-cli
pip install -e .
```

**依赖**：`click>=8.1`（自动安装）+ `curl`（大多数系统已预装）

## ⚙️ 快速配置

### 首次使用（交互式引导）

```bash
fns login
# 输入 FNS 服务器地址: https://your-server
# 用户名或邮箱: you@example.com
# 密码: **** (隐藏输入)
# 📦 可用 Vault:
#   1. defaultVault
# 选择 Vault [1]: 1
# 🎉 配置完成! 试试: fns list
```

### 脚本模式（非交互）

```bash
fns login -u https://your-server username password
```

### 手动配置

```bash
fns config url "https://your-server/api"
```

## 🚀 命令参考

### 认证与配置
```bash
fns login [用户] [密码] [-u URL]   # 登录（省略参数时交互式）
fns config show                    # 查看当前配置
fns config url <值>                # 设置 API 地址
fns config vault <值>              # 设置 Vault 名称
```

### 笔记 CRUD
```bash
fns read <路径>                     # 读取笔记
fns write <路径> <内容|@文件>       # 创建/覆盖（使用 @ 上传本地文件）
fns append <路径> <内容|@文件>      # 追加内容（智能换行处理）
fns prepend <路径> <内容|@文件>     # 在开头插入内容（Frontmatter 后）
fns delete <路径>                   # 删除笔记（移入回收站）
fns move <旧路径> <新路径>          # 移动/重命名笔记
fns replace <路径> <查找> <替换>    # 查找替换（支持正则）
fns history <路径>                  # 查看修订历史
fns restore <路径>                  # 从回收站恢复笔记
```

### 知识与链接
```bash
fns list [关键词]                    # 列出/搜索笔记
fns tree [路径]                      # 查看目录树结构
fns backlinks <路径>                 # 链接到当前笔记的笔记
fns outlinks <路径>                  # 当前笔记链接到的笔记
```

### 文件夹管理
```bash
fns mkdir <路径>                     # 创建文件夹
fns folder <路径>                    # 查看文件夹信息
fns folder-list [路径]               # 列出子文件夹
fns folder-files <路径>              # 列出文件夹内的文件
fns folder-notes <路径>              # 列出文件夹内的笔记
fns folder-tree [--depth N]          # 查看文件夹树
fns folder-delete <路径>             # 删除文件夹（软删除）
```

### 文件/附件管理
```bash
fns file-info <路径>                 # 查看文件元数据
fns file-download <路径> [-o 文件]   # 下载文件到本地
fns file-list [关键词]               # 分页列出文件
fns file-delete <路径>               # 删除文件（移入回收站）
fns file-rename <旧> <新>            # 重命名文件
fns file-restore <路径>              # 从回收站恢复文件
fns file-recycle-clear [路径]        # 清空文件回收站
```

### 分享与元数据
```bash
fns share <路径> [--expire 24h] [--password 密码]  # 创建分享链接
fns unshare <路径>                   # 取消分享
fns frontmatter <路径>               # 查看 Frontmatter
fns frontmatter <路径> --set key=value --remove key  # 编辑 Frontmatter
```

### Vault 与服务器
```bash
fns vaults                           # 列出可用 Vault
fns vault-info [id]                  # 查看 Vault 详情
fns vault-create <名称>              # 创建 Vault（需确认）
fns vault-delete <id>                # 删除 Vault（二次确认）
fns recycle-bin [关键词]             # 查看回收站
fns version                          # 查看服务器版本
fns health                           # 检查服务器健康状态
fns info                             # 查看当前用户信息
```

### 全局标志
```bash
fns --json <命令>                    # JSON 格式输出（适合 AI/脚本解析）
fns --quiet <命令>                   # 静默模式
fns --version / -v                   # 显示版本
fns --help                           # 显示帮助
```

## 🤖 AI Agent 集成

本工具旨在为 AI Agent 提供**长期记忆和知识访问能力**：

- **读取上下文**：编码任务前 `fns read` 相关笔记获取背景信息
- **自动文档**：`fns append` 将变更记录追加到日记
- **知识检索**：`fns list` / `fns tree` 发现相关文件
- **知识图谱**：`fns backlinks` / `fns outlinks` 查找关联笔记

**AI Agent 示例：**
```bash
# 让 AI 读取上下文、工作、然后记录
fns read "projects/架构设计.md" --json
# ... AI 工作 ...
fns append "daily/2024-05-20.md" "- 完成架构评审"
```

## 📁 目录结构

```
fns-cli/
├── fns.py              # 核心 CLI 逻辑
├── setup.py            # 安装脚本
├── requirements.txt    # 依赖列表
├── tests/
│   └── test_fns.py     # 单元测试
├── README.md           # 英文说明
├── README.zh.md        # 本文件
├── skill.md            # 使用示例
├── CHANGELOG.md        # 版本历史
└── LICENSE             # MIT 协议
```

## 📖 使用示例

详细示例请参见可移植的 Skill：[`fns-skill/SKILL.md`](fns-skill/SKILL.md)。你可以直接将整个 `fns-skill/` 目录复制到你自己的 AI Agent 的 Skills 文件夹中（Qwen Code、Claude Code 等）。

## 🧪 运行测试

```bash
python -m unittest discover -s tests -v
```

## 🔗 相关项目

- **[fast-note-sync-service](https://github.com/haierkeys/fast-note-sync-service)** — FNS 后端服务
- **[obsidian-fast-note-sync](https://github.com/haierkeys/obsidian-fast-note-sync)** — Obsidian 插件

## 📜 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。
